#!/bin/bash
# MARK XXXIX - Background Clap Listener con auto-reinicio
# Se ejecuta en background, espera 2 aplausos y lanza JARVIS
# Luego se reinicia automáticamente para esperar más aplausos

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

source .venv/bin/activate

export DISPLAY=:1
export WAYLAND_DISPLAY=wayland-1
export XDG_RUNTIME_DIR=/run/user/1000
export QT_QPA_PLATFORM=wayland

LOG_FILE="/tmp/mark-xxxix-clap.log"

# Verificar si ya hay un loop corriendo
if [ -f /tmp/mark-xxxix-clap-loop.pid ]; then
    OLD_PID=$(cat /tmp/mark-xxxix-clap-loop.pid 2>/dev/null)
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
        echo "[$(date)] Clap listener already running (PID: $OLD_PID)" >> "$LOG_FILE"
        exit 0
    fi
fi

# Iniciar el loop en background
exec bash clap_listener_loop.sh &
echo $! > /tmp/mark-xxxix-clap-loop.pid

echo "[$(date)] MARK XXXIX clap listener started (PID: $!)" >> "$LOG_FILE"