#!/bin/bash

# Adiciona o diretório da libpulsecommon ao LD_LIBRARY_PATH
# O caminho pode variar ligeiramente, mas este é o mais comum para a libpulse0 no Heroku
export LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu/pulseaudio:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH" # Pode ser necessário para outras libs
echo "-----> LD_LIBRARY_PATH configurado: $LD_LIBRARY_PATH"

# Opcional: Verificar se o FFmpeg ainda tem problemas de dependência
# ffmpeg -v debug -i /dev/null -f null - 2>&1 | grep "loading shared libraries"