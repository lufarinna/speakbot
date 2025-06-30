import os
import asyncio
import subprocess # Adicionado para chamar o FFmpeg diretamente
from telegram import Update, Voice, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
import google.generativeai as genai
# from pydub import AudioSegment # Removido/Comentado
from dotenv import load_dotenv
from gtts import gTTS
import random
import re

# Importações adicionais para Webhook
from flask import Flask, request, jsonify
import logging

# Configuração de logging para Flask e Telegram
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Carrega variáveis do ambiente ---
load_dotenv(dotenv_path=".env")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# Para webhooks, você precisará de uma URL base para seu bot
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://bot.educaingles.com.br/telegram_webhook") # URL do seu domínio + rota do webhook

genai.configure(api_key=GOOGLE_API_KEY)

# --- Temas disponíveis ---
TEMAS = {
    "viagem": "🛫 Viagem e Aeroporto",
    "restaurante": "🍽️ Restaurantes e Alimentação",
    "hotel": "🏨 Hotel e Acomodação",
    "compras": "🛍️ Compras",
    "transporte": "🚕 Transportes e Deslocamento",
    "conversas": "👥 Conversas Cotidianas"
}

# --- Formatação para HTML ---
def format_to_html(text: str) -> str:
    text = text.replace('&', '&amp;')
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
    return text

# --- Gera áudio com gTTS ---
async def generate_tts(text: str, filename: str = "output.mp3") -> str:
    try:
        tts = gTTS(text=text, lang="en", tld="com")
        tts.save(filename)
        return filename
    except Exception as e:
        logger.error(f"Erro no gTTS: {e}")
        return None

# --- Menu principal com botões de temas ---
async def menu_principal(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"tema_{chave}")]
        for chave, label in TEMAS.items()
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(
            "👋 Olá! Escolha um tema para praticar sua pronúncia:",
            reply_markup=reply_markup
        )
    elif update.callback_query:
        await update.callback_query.message.reply_text(
            "👋 Olá! Escolha um tema para praticar sua pronúncia:",
            reply_markup=reply_markup
        )

# --- Gera frase com IA com base no tema ---
async def sugerir_frase_por_tema(update: Update, context: CallbackContext, tema_chave: str):
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = (
        f"Escolha uma frase curta, simples e útil para treinar pronúncia em inglês. "
        f"O tema é '{TEMAS[tema_chave]}'. "
        f"A frase deve ter no máximo 10 palavras. "
        f"Responda apenas com a frase, sem explicações."
    )

    try:
        response = model.generate_content(prompt)
        frase = response.text.strip().strip('"')
        context.user_data["frase"] = frase
        context.user_data.setdefault("score", 0)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"<b>🎤 Repita esta frase:</b>\n\n👉 <code>{frase}</code>\n\nGrave um áudio com sua pronúncia!",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Erro ao gerar frase: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Erro ao gerar frase: {e}")

# --- Avaliação de pronúncia ---
async def avaliar_pronuncia(update: Update, context: CallbackContext) -> None:
    if "frase" not in context.user_data:
        await update.message.reply_text("⚠️ Por favor, escolha um tema antes de enviar sua voz.")
        return

    user = update.effective_user
    voice: Voice = update.message.voice
    ogg_path = f"/tmp/voz_{user.id}.ogg" # Usar /tmp para arquivos temporários na VM
    wav_path = f"/tmp/voz_{user.id}.wav" # Usar /tmp para arquivos temporários na VM

    try:
        voice_file = await voice.get_file()
        await voice_file.download_to_drive(ogg_path)
        logger.info(f"Áudio OGG baixado para {ogg_path}")

        await update.message.reply_text("🔄 Processando seu áudio... Por favor, aguarde!")

        # Bloco de conversão de áudio usando subprocess para chamar FFmpeg diretamente
        command = [
            "ffmpeg", 
            "-i", ogg_path, 
            "-acodec", "pcm_s16le", 
            "-ar", "16000", 
            "-nostats", 
            "-threads", "1", 
            wav_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_message = stderr.decode()
            logger.error(f"FFmpeg falhou com erro: {error_message}")
            raise Exception(f"FFmpeg falhou com erro: {error_message}")
        logger.info(f"✅ Áudio convertido de OGG para WAV com FFmpeg via subprocess.")

    except Exception as e:
        logger.error(f"Erro ao processar o áudio com FFmpeg: {e}")
        await update.message.reply_text(f"❌ Erro ao processar o áudio com FFmpeg: {e}")
        return
    finally:
        for path in [ogg_path, wav_path]:
            if os.path.exists(path):
                os.remove(path)
                logger.info(f"Arquivo temporário removido: {path}")


    frase_original = context.user_data["frase"]
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt_text = (
        f"AVALIE a pronúncia do usuário para a frase em inglês: '{frase_original}'.\n\n"
        "Forneça:\n"
        "1. Uma avaliação geral de 1 a 5 estrelas ⭐.\n"
        "2. Pontos específicos para melhorar (fonemas, entonação).\n"
        "3. Uma transcrição fonética **simplificada** com sons do português.\n"
        "4. Uma transcrição textual do que foi ouvido.\n\n"
        "Use **negrito** para destacar. Seja motivador e direto."
    )

    try:
        await update.message.reply_text("🤖 Analisando sua pronúncia com Google Gemini... Aguarde só um instante!")
        audio_part = genai.upload_file(wav_path, mime_type="audio/wav")
        response = model.generate_content([prompt_text, audio_part])
        feedback_raw = response.text
        feedback = format_to_html(feedback_raw)

        partes = re.split(r'\n?(\d\.\s)', feedback)
        blocos = [''.join(par) for par in zip(partes[1::2], partes[2::2])] if len(partes) > 2 else [feedback]

        stars = min(5, max(1, feedback.count("⭐")))
        context.user_data["score"] += stars
        total_score = context.user_data["score"]

        await update.message.reply_text(
            f"<b>📌 Frase Avaliada:</b> <code>{frase_original}</code>",
            parse_mode="HTML"
        )

        for bloco in blocos:
            await update.message.reply_text(bloco.strip(), parse_mode="HTML")

        tts_file = await generate_tts(frase_original)
        if tts_file:
            await update.message.reply_voice(voice=open(tts_file, "rb"))
            os.remove(tts_file)

        await update.message.reply_text(
            f"🏆 <b>Pontuação total:</b> {total_score} pontos.\n\n"
            "🎤 Você pode tentar repetir ou escolher um novo tema.",
            parse_mode="HTML"
        )

        keyboard = [
            [InlineKeyboardButton("🔁 Repetir a Frase", callback_data="repetir_frase")],
            [InlineKeyboardButton("🆕 Novo Tema", callback_data="novo_tema")],
            [InlineKeyboardButton("📊 Meu Progresso", callback_data="progresso")]
        ]
        await update.message.reply_text("O que deseja fazer agora?", reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        logger.error(f"Erro na avaliação: {e}")
        await update.message.reply_text(f"❌ Erro na avaliação: {str(e)[:200]}")
    finally:
        for path in [ogg_path, wav_path]:
            if os.path.exists(path):
                os.remove(path)


# --- Callback de botões ---
async def botao_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("tema_"):
        tema_escolhido = data.replace("tema_", "")
        context.user_data["tema"] = tema_escolhido
        await sugerir_frase_por_tema(update, context, tema_escolhido)

    elif data == "novo_tema":
        await menu_principal(update, context)

    elif data == "repetir_frase":
        frase = context.user_data.get("frase")
        if frase:
            await query.message.reply_text(
                f"<b>🎤 Repita esta frase novamente:</b>\n\n👉 <code>{frase}</code>\n\n"
                "🎤 Grave outro áudio com sua pronúncia para tentar de novo.",
                parse_mode="HTML"
            )
        else:
            await query.message.reply_text("⚠️ Nenhuma frase encontrada. Escolha um tema.")

    elif data == "progresso":
        pontos = context.user_data.get("score", 0)
        await query.message.reply_text(f"📊 Sua pontuação atual é: {pontos} pontos.")

# --- Comando /start ---
async def start(update: Update, context: CallbackContext):
    await menu_principal(update, context)

# --- Main (para Webhook) ---
# Instância Flask para receber webhooks
app = Flask(__name__)

@app.route('/telegram_webhook', methods=['POST'])
async def telegram_webhook_handler():
    # Obtém o JSON da requisição do Telegram
    update_json = request.get_json(force=True)
    logger.info(f"Webhook recebido: {update_json}")

    # Cria um objeto Update a partir do JSON e o coloca na fila de processamento do bot
    # Certifique-se de que 'application' está acessível aqui (definido no main)
    try:
        update = Update.de_json(update_json, application.bot)
        await application.process_update(update) # Usa process_update para lidar com a atualização
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def main():
    logger.info("🎙️ Bot de Pronúncia Iniciado (Modo Webhook)...")
    # Crie a aplicação do Telegram
    telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Adicione os handlers
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.VOICE, avaliar_pronuncia))
    telegram_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), menu_principal))
    telegram_app.add_handler(CallbackQueryHandler(botao_callback))

    # Configura o webhook
    # A porta 5000 será usada pelo Gunicorn para servir o Flask app
    # O url_path deve corresponder à rota no Flask (@app.route('/telegram_webhook'))
    # O webhook_url é o que você vai registrar no Telegram
    telegram_app.run_webhook(
        listen="0.0.0.0",
        port=5000, # A porta que o Gunicorn vai escutar
        url_path="telegram_webhook", # A rota que o Telegram vai enviar as atualizações
        webhook_url=WEBHOOK_URL # A URL completa que o Telegram vai usar
    )

    # O Flask app (variável 'app') será executado pelo Gunicorn
    # Não chame app.run() aqui, pois o Gunicorn fará isso.

if __name__ == "__main__":
    # Esta parte só será executada se você rodar o script diretamente (não com Gunicorn)
    # Em produção, o Gunicorn vai chamar o 'app' Flask diretamente.
    # Para testes locais, você pode descomentar e rodar app.run()
    # main() # Não chame main() aqui, o Gunicorn vai chamar o Flask app.
    pass # Deixe vazio ou adicione um logger.info("Rodando via Gunicorn")
