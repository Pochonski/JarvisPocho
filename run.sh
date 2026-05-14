#!/bin/bash
# MARK XXXIX - Launcher Script (Optimizado para Hyprland/Linux)
# Uso: ./run.sh              → ejecuta app normalmente
#        ./run.sh --listen    → espera 2 aplausos para iniciar

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activar venv
source .venv/bin/activate

# Definir XDG vars si no están definidas
export XDG_DESKTOP_DIR="${XDG_DESKTOP_DIR:-$HOME/Desktop}"
export XDG_DOWNLOAD_DIR="${XDG_DOWNLOAD_DIR:-$HOME/Downloads}"
export XDG_DOCUMENTS_DIR="${XDG_DOCUMENTS_DIR:-$HOME/Documents}"
export XDG_PICTURES_DIR="${XDG_PICTURES_DIR:-$HOME/Pictures}"
export XDG_MUSIC_DIR="${XDG_MUSIC_DIR:-$HOME/Music}"
export XDG_VIDEOS_DIR="${XDG_VIDEOS_DIR:-$HOME/Videos}"

# Variables de entorno para Hyprland/Wayland
export DISPLAY=:1
export WAYLAND_DISPLAY=wayland-1
export XDG_RUNTIME_DIR=/run/user/1000
export QT_QPA_PLATFORM=wayland

# Verificar API key
if [ ! -f config/api_keys.json ]; then
    echo "ERROR: config/api_keys.json no existe"
    exit 1
fi

# Verificar face.png
if [ ! -f face.png ]; then
    echo "ADVERTENCIA: face.png no encontrado"
fi

if [ "$1" = "--listen" ] || [ "$1" = "-l" ]; then
    echo "
╔═══════════════════════════════════════════╗
║  👏 ESCUCHANTANDO APLAUSOS...            ║
║  2 aplausos = iniciar JARVIS             ║
║  Ctrl+C para salir                       ║
╚═══════════════════════════════════════════╝
"
    python clap_detector.py
else
    echo "
╔═══════════════════════════════════════╗
║      🤖 JARVIS - INITIALIZING     ║
╚═══════════════════════════════════════╝
"
    python main.py
fi