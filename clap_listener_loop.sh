#!/bin/bash
# MARK XXXIX - Clap Listener con auto-reinicio
# Espera 2 aplausos para lanzar JARVIS, luego se reinicia

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

source .venv/bin/activate

export DISPLAY="${DISPLAY:-:0}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export QT_QPA_PLATFORM=xcb

LOG_FILE="/tmp/mark-xxxix-clap.log"

echo "[$(date)] MARK XXXIX clap listener starting..." >> "$LOG_FILE"

while true; do
    # Verificar si ya hay un main.py corriendo
    if pgrep -f "python main.py" > /dev/null 2>&1; then
        echo "[$(date)] JARVIS already running, waiting..." >> "$LOG_FILE"
        sleep 5
        continue
    fi

    # Iniciar clap detector en foreground (se bloquea hasta detectar o error)
    python clap_detector.py >> "$LOG_FILE" 2>&1
    CLAP_EXIT=$?

    if [ $CLAP_EXIT -eq 0 ]; then
        # Clap detectado - JARVIS fue lanzado
        echo "[$(date)] Clap detected, JARVIS launched, waiting for it to close..." >> "$LOG_FILE"

        # Esperar a que main.py termine
        while pgrep -f "python main.py" > /dev/null 2>&1; do
            sleep 1
        done

        echo "[$(date)] JARVIS closed, restarting clap listener..." >> "$LOG_FILE"
        sleep 2
    else
        # Error o interrupción - reiniciar después de un delay
        echo "[$(date)] Clap detector exited (code $CLAP_EXIT), restarting..." >> "$LOG_FILE"
        sleep 2
    fi
done