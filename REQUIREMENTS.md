# MARK XXXIX - Requirements

## System

- **OS**: Linux (Arch Linux with Hyprland tested)
- **Python**: 3.11 or 3.14
- **Desktop**: Hyprland / Wayland
- **Display**: :1

## Python Packages

Core dependencies (install via `pip install -r requirements.txt`):

| Package | Purpose |
|--------|---------|
| sounddevice | Audio input/output |
| google-genai | Gemini API client |
| google-generativeai | Legacy Gemini API |
| PyQt6 | GUI interface |
| pyautogui | Keyboard/mouse control |
| pyperclip | Clipboard access |
| psutil | System metrics |
| opencv-python | Screen processing |
| numpy | Audio processing |
| mss | Screenshot capture |
| playwright | Browser automation |
| requests | HTTP requests |
| beautifulsoup4 | Web scraping |
| duckduckgo-search | Web search |
| python-pptx | PowerPoint files |
| youtube-transcript-api | YouTube transcripts |
| send2trash | Safe file deletion |

## System Packages (optional)

For full functionality:

```bash
# Audio/Video
sudo pacman -S gst-libav gst-plugins-base  # GStreamer for audio

# Screen capture
sudo pacman -S scrot gnome-screenshot     # Screenshot tools

# Window management
sudo pacman -S wmctrl xdotool             # Window control

# Display
sudo pacman -S xclip xdotool               # Clipboard/X11 utils
```

## Environment Variables

Set automatically by `run.sh` and `start-clap-listener.sh`:

```bash
export DISPLAY=:1
export WAYLAND_DISPLAY=wayland-1
export XDG_RUNTIME_DIR=/run/user/1000
export QT_QPA_PLATFORM=wayland
export XDG_DESKTOP_DIR=$HOME/Desktop
export XDG_DOWNLOAD_DIR=$HOME/Downloads
export XDG_DOCUMENTS_DIR=$HOME/Documents
export XDG_PICTURES_DIR=$HOME/Pictures
export XDG_MUSIC_DIR=$HOME/Music
export XDG_VIDEOS_DIR=$HOME/Videos
```

## Files

### Required
- `config/api_keys.json` - Must contain: `{"gemini_api_key": "YOUR_KEY", "os_system": "linux"}`
- `face.png` - JARVIS avatar image (256x256 PNG)

### Created automatically
- `.venv/` - Python virtual environment
- `memory/long_term.json` - User memory (created on first run)

## Hardware

- **Microphone** - Required for voice input and clap detection
- **Speaker** - Required for JARVIS audio output

## Optional Services

### Systemd (auto-start clap listener on boot)

```bash
systemctl --user enable mark-xxxix-clap
systemctl --user start mark-xxxix-clap
```

## Quick Install

```bash
cd ~/Projects/Mark-XXXIX
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Port Conflicts

If port issues occur, verify no other process using:
```bash
ps aux | grep -E "python|sounddevice" | grep -v grep
```