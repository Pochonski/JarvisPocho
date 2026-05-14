# MARK XXXIX - Clap Listener Documentation

## Overview

MARK XXXIX puede iniciarse aplaudiendo 2 veces. Un listener corre en background y detecta los claps para lanzar la aplicación.

## Files

| File | Purpose |
|------|---------|
| `clap_detector.py` | Módulo de detección de aplausos |
| `clap_listener_loop.sh` | Loop que reinicia el listener automáticamente |
| `start-clap-listener.sh` | Script para iniciar el listener en background |
| `run.sh` | Launcher principal de JARVIS |

## Quick Start

### Start clap listener (background)
```bash
cd ~/Projects/Mark-XXXIX
./start-clap-listener.sh
```

### View logs
```bash
tail -f /tmp/mark-xxxix-clap.log
```

### Check if running
```bash
ps aux | grep -E "clap|main.py" | grep -v grep
```

## Configuration

### Clap Detection Settings

Edit `clap_detector.py` lines 14-20 to adjust:

```python
detector = ClapDetector(
    clap_count=2,       # Number of claps to detect
    clap_window=1.5,    # Seconds window for claps
    threshold=0.6,      # Volume threshold (0.0=sensitive, 1.0=low)
    sample_rate=16000,  # Audio sample rate
    warmup_time=1.0,    # Seconds to ignore audio at start
)
```

### Adjustable Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `clap_count` | 2 | Number of claps required |
| `clap_window` | 1.5s | Time window to detect claps |
| `threshold` | 0.6 | Volume threshold (higher = less sensitive) |
| `warmup_time` | 1.0s | Ignore audio at startup |
| debounce | 0.2s | Min time between claps |

## Systemd Service (Optional)

For auto-start on boot:

```bash
# Enable service
systemctl --user enable mark-xxxix-clap

# Start service
systemctl --user start mark-xxxix-clap

# Check status
systemctl --user status mark-xxxix-clap

# Stop service
systemctl --user stop mark-xxxix-clap
```

### Service files
- Service definition: `~/.config/systemd/user/mark-xxxix-clap.service`
- Startup script: `./start-clap-listener.sh`

## Troubleshooting

### Clap listener not starting
```bash
cd ~/Projects/Mark-XXXIX
chmod +x start-clap-listener.sh
./start-clap-listener.sh
```

### Too many false triggers
Increase threshold in `clap_detector.py`:
```python
threshold=0.8  # Higher = less sensitive
```

### Not sensitive enough
Decrease threshold:
```python
threshold=0.3  # Lower = more sensitive
```

### View real-time audio levels (debug)
```bash
source .venv/bin/activate
python3 -c "
import numpy as np
import sounddevice as sd

def callback(indata, frames, time_info, status):
    volume = np.sqrt(np.mean(indata ** 2))
    bar = '#' * int(volume * 100)
    print(f'Volume: {volume:.3f} {bar}')

stream = sd.InputStream(samplerate=16000, channels=1, dtype='float32', callback=callback)
stream.start()
input('Press Enter to stop...')
"
```

### Clear all processes
```bash
pkill -9 -f "clap" 2>/dev/null
pkill -9 -f "main.py" 2>/dev/null
rm -f /tmp/mark-xxxix-clap*.pid
```

## Flow Diagram

```
User applauds 2x
       ↓
clap_detector.py detects
       ↓
launch_on_clap() triggered
       ↓
run.sh starts main.py
       ↓
JARVIS UI opens
       ↓
User closes JARVIS
       ↓
clap_listener_loop.sh detects main.py closed
       ↓
Restart clap detector (wait for next 2 claps)
```

## Log Location

All logs are written to: `/tmp/mark-xxxix-clap.log`

Example log entries:
```
[Wed May 13 07:33:55 AM CST 2026] Clap detected, JARVIS launched, waiting for it to close...
[Wed May 13 07:33:57 AM CST 2026] JARVIS closed, restarting clap listener...
```

## Environment Variables

Required for Hyprland/Wayland:
- `DISPLAY=:1`
- `WAYLAND_DISPLAY=wayland-1`
- `XDG_RUNTIME_DIR=/run/user/1000`
- `QT_QPA_PLATFORM=wayland`

These are set automatically in `start-clap-listener.sh` and `clap_listener_loop.sh`.