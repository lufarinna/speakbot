#!/bin/bash

# URL para o FFmpeg estático
FFMPEG_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"

# Pasta onde o FFmpeg será extraído e movido
FFMPEG_DIR="/app/vendor/ffmpeg"

echo "-----> Baixando e configurando FFmpeg estático..."

# Cria o diretório de destino se não existir
mkdir -p "$FFMPEG_DIR"

# Baixa e extrai o FFmpeg
curl -L "$FFMPEG_URL" | tar xJ -C "$FFMPEG_DIR" --strip-components=1

# Verifica se a extração foi bem-sucedida
if [ $? -ne 0 ]; then
    echo " !     Erro: Falha ao baixar ou extrair FFmpeg."
    exit 1
fi

# Adiciona o diretório do FFmpeg ao PATH.
export PATH="$FFMPEG_DIR:$PATH"
echo "-----> FFmpeg configurado com sucesso no PATH."