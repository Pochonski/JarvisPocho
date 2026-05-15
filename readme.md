# JarvisPocho

### Your Personal AI Assistant with Tico Soul

> A real-time voice AI that can hear, see, understand, and control your computer. Built for **Arch Linux + Hyprland (Omarchy)** with Gemini 2.5 Flash.

---

## Overview

JarvisPocho is a personalized fork of the MARK XXXIX project, transformed into a fully autonomous desktop assistant that lives on your machine. It combines **real-time voice conversation**, **screen vision**, **file processing**, **browser automation**, and **full system control** into a single, always-ready assistant.

Unlike cloud-only assistants, JarvisPocho runs locally, executes tools directly on your machine, remembers your preferences across sessions, and can be launched with just **two claps**.

---

## Features

| Feature | Description |
|---------|-------------|
| Real-time Voice | Ultra-low latency conversation with audio streaming (no typing needed) |
| Screen Vision | Analyzes your screen or webcam in real-time using Gemini vision |
| System Control | Launch apps, manage files, control volume, brightness, WiFi, and more |
| Browser Automation | Navigate websites, click elements, fill forms, take screenshots |
| File Processing | Analyze PDFs, images, code files, spreadsheets, audio, video, and more |
| Autonomous Tasks | Multi-step planning with priority-based task queue |
| Persistent Memory | Remembers your identity, preferences, projects, relationships, and goals |
| Clap Listener | Launch the assistant with two claps |
| Cross-platform | Works on Windows, macOS, and Linux (optimized for Hyprland/Wayland) |

---

## Architecture

```
JarvisPocho/
├── main.py                  # Entry point — connects to Gemini Live API
├── ui.py                    # PyQt6 interface with animated avatar
├── file_picker.py           # File upload handler
├── run.sh                   # Main launcher script
├── setup.py                 # Initial setup wizard
│
├── core/
│   └── prompt.txt           # System prompt (personality, rules, tool routing)
│
├── actions/                 # Tool implementations (18+ tools)
│   ├── open_app.py          # Launch any application
│   ├── web_search.py        # Web search with DuckDuckGo
│   ├── weather_report.py    # Weather reports
│   ├── send_message.py      # WhatsApp/Telegram messaging
│   ├── reminder.py          # Timed reminders via Task Scheduler
│   ├── youtube_video.py     # Play, summarize, or get info on YouTube videos
│   ├── screen_processor.py  # Screen capture + Gemini vision analysis
│   ├── computer_settings.py # Volume, brightness, WiFi, dark mode, window management
│   ├── computer_control.py  # Type, click, hotkeys, screenshots, AI element finder
│   ├── browser_control.py   # Full browser automation (Chrome, Edge, Firefox, etc.)
│   ├── file_controller.py   # File/folder management (list, create, delete, move, etc.)
│   ├── file_processor.py    # Process uploaded files (PDF, images, code, audio, video)
│   ├── desktop.py           # Wallpaper, organize, clean desktop
│   ├── code_helper.py       # Write, edit, explain, run, or build code
│   ├── dev_agent.py         # Build multi-file projects from scratch
│   ├── game_updater.py      # Steam/Epic game management
│   ├── flight_finder.py     # Search Google Flights
│   └── reminder.py          # Set timed reminders
│
├── agent/                   # Autonomous task execution
│   ├── planner.py           # Breaks goals into step-by-step plans
│   ├── executor.py          # Executes planned steps
│   ├── task_queue.py        # Priority-based task queue (HIGH/NORMAL/LOW)
│   └── error_handler.py     # Handles and recovers from step failures
│
├── memory/                  # Long-term memory system
│   ├── memory_manager.py    # Load, save, update, and format memory
│   ├── config_manager.py    # Memory configuration
│   └── long_term.json       # Persistent user memory (auto-created)
│
├── config/
│   └── api_keys.json        # Gemini API key and OS configuration
│
├── clap_detector.py         # Clap detection from microphone input
├── clap_listener_loop.sh    # Auto-restart loop for clap listener
├── start-clap-listener.sh   # Start clap listener in background
└── CLAP_LISTENER.md         # Full clap listener documentation
```

---

## Tools & Capabilities

### Application Control
- **`open_app`** — Launch any application by name (Chrome, Spotify, VS Code, etc.)
- **`computer_settings`** — Volume, brightness, WiFi, dark mode, window management, keyboard shortcuts, power controls
- **`computer_control`** — Type text, click, hotkeys, scroll, screenshots, AI element finder on screen

### Web & Browser
- **`web_search`** — Search the web (DuckDuckGo), compare items
- **`browser_control`** — Full browser automation: navigate, click, fill forms, screenshots, multi-browser support
- **`youtube_video`** — Play videos, summarize content, get video info, show trending

### Files & Desktop
- **`file_controller`** — List, create, delete, move, copy, rename, read, write, find files
- **`file_processor`** — Process uploaded files: PDFs, images, code, spreadsheets, audio, video, archives
- **`desktop_control`** — Change wallpaper, organize icons, clean desktop, view stats

### Communication
- **`send_message`** — Send messages via WhatsApp or Telegram
- **`reminder`** — Set timed reminders using Task Scheduler

### Development
- **`code_helper`** — Write, edit, explain, run, build, or document code
- **`dev_agent`** — Build complete multi-file projects from scratch

### Utilities
- **`weather_report`** — Get weather for any city
- **`screen_process`** — Capture screen or webcam and analyze with Gemini vision
- **`game_updater`** — Manage Steam/Epic games (install, update, schedule downloads)
- **`flight_finder`** — Search Google Flights for best options
- **`agent_task`** — Execute complex multi-step tasks with autonomous planning
- **`save_memory`** — Save important facts about the user to long-term memory
- **`shutdown_jarvis`** — Shut down the assistant

---

## Agent System

JarvisPocho can autonomously execute complex multi-step tasks through its agent system:

1. **Planner** — Breaks a goal into a sequence of steps using available tools (max 5 steps)
2. **Executor** — Executes each step in order, with error recovery
3. **Task Queue** — Priority-based queue (HIGH > NORMAL > LOW) with concurrent execution
4. **Error Handler** — Detects failures, replans, and retries automatically

Example: *"Research mechanical engineering and save it to a notepad file"*
- Step 1: `web_search` — "mechanical engineering overview"
- Step 2: `web_search` — "mechanical engineering applications and trends"
- Step 3: `file_controller` — Write results to desktop

---

## Memory System

JarvisPocho remembers important information about you across sessions. Memory is stored in `memory/long_term.json` and automatically formatted into the system prompt.

### Categories

| Category | What it stores |
|----------|---------------|
| **identity** | Name, age, birthday, city, job, language, nationality |
| **preferences** | Favorite food, color, music, hobbies, settings |
| **projects** | Active projects, goals, things being built |
| **relationships** | Friends, family, partner, colleagues |
| **wishes** | Future plans, travel dreams, things to buy |
| **notes** | Habits, schedule, anything else worth remembering |

Memory is automatically trimmed to stay within the prompt limit (2200 chars). Oldest entries are removed first.

---

## Clap Listener

Launch JarvisPocho by clapping **twice**. A background listener monitors your microphone and launches the assistant when it detects two claps within a time window.

```bash
# Start clap listener (runs in background)
./start-clap-listener.sh

# View logs
tail -f /tmp/mark-xxxix-clap.log

# Kill all processes
pkill -9 -f "clap" 2>/dev/null
pkill -9 -f "main.py" 2>/dev/null
```

### Configuration

Edit `clap_detector.py` to adjust sensitivity:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `clap_count` | 2 | Number of claps required |
| `clap_window` | 1.5s | Time window to detect claps |
| `threshold` | 0.6 | Volume threshold (higher = less sensitive) |

---

## Customizations

This fork includes personalized enhancements over the original MARK XXXIX project:

### Tico Personality
Costa Rican speaking style with natural expressions like "pura vida" and "mae". The assistant is warm and friendly while staying efficient and professional. Uses more tico expressions when speaking Spanish, keeps them subtle in English.

### Language Control
Responses are restricted to **Spanish and English only**. If the audio transcription seems garbled or in another language (Portuguese, French, Italian, etc.), the assistant ignores it and waits for clear input. Spanish is the default when in doubt.

### Wayland Input Support
Full keyboard input support for **Wayland/Hyprland** using `wtype`:
- Text typing via `wtype` (works in all Wayland apps)
- Key pressing via `wtype -k` with proper key mapping (Enter, Escape, Tab, arrows, F-keys, etc.)
- Clipboard paste via `wl-copy` + `Super+V`

### Window Management
- **Close active window** — Uses `hyprctl dispatch killactive` (Hyprland native)
- **Close window by name** — Uses `hyprctl clients -j` to find and close specific windows by title
- **SUPER+W** hotkey added to `_HOTKEY_COMMANDS` for direct window closing

### Environment Variables
Fixed environment variables for **Hyprland/Omarchy** compatibility:
- `DISPLAY` defaults to `:0` (respects existing value)
- `XDG_RUNTIME_DIR` uses current user ID dynamically
- `QT_QPA_PLATFORM` set to `xcb` for PyQt6 compatibility

### Terminal Launch
Removed broken terminal alias. Terminal is now launched via `SUPER+RETURN` through the `computer_control` hotkey system.

---

## Installation

### Prerequisites

- **OS**: Arch Linux with Hyprland (Omarchy) — also supports Windows and macOS
- **Python**: 3.11 or 3.14
- **Microphone**: Required for voice input and clap detection
- **Speaker**: Required for audio output
- **API Key**: Free [Gemini API key](https://aistudio.google.com/apikey)

### Step 1: Clone

```bash
git clone https://github.com/Pochonski/JarvisPocho.git
cd JarvisPocho
```

### Step 2: Install Dependencies

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install

# Install system packages (Arch Linux)
sudo pacman -S wtype wl-clipboard gst-libav gst-plugins-base
```

### Step 3: Configure API Key

```bash
# Option A: Run setup wizard
python setup.py

# Option B: Create manually
mkdir -p config
cat > config/api_keys.json << 'EOF'
{
  "gemini_api_key": "YOUR_API_KEY_HERE",
  "os_system": "linux"
}
EOF
```

### Step 4: Run

```bash
# Direct launch
./run.sh

# Or with clap listener (clap twice to launch)
./start-clap-listener.sh
```

---

## Requirements

### Python Packages

| Package | Purpose |
|---------|---------|
| `sounddevice` | Audio input/output |
| `google-genai` | Gemini API client |
| `google-generativeai` | Legacy Gemini API |
| `PyQt6` | GUI interface |
| `pyautogui` | Keyboard/mouse control |
| `pyperclip` | Clipboard access |
| `psutil` | System metrics |
| `opencv-python` | Screen processing |
| `numpy` | Audio processing |
| `mss` | Screenshot capture |
| `playwright` | Browser automation |
| `requests` | HTTP requests |
| `beautifulsoup4` | Web scraping |
| `duckduckgo-search` | Web search |
| `python-pptx` | PowerPoint files |
| `youtube-transcript-api` | YouTube transcripts |
| `send2trash` | Safe file deletion |
| `evdev` | Low-level input (optional) |

### System Packages (Arch Linux)

```bash
# Audio/Video
sudo pacman -S gst-libav gst-plugins-base

# Clipboard
sudo pacman -S wl-clipboard

# Keyboard input for Wayland
sudo pacman -S wtype

# Window management
sudo pacman -S wmctrl xdotool

# Screenshots
sudo pacman -S scrot gnome-screenshot
```

---

## Configuration

### API Keys (`config/api_keys.json`)

```json
{
  "gemini_api_key": "YOUR_API_KEY",
  "os_system": "linux"
}
```

### Environment Variables

Set automatically by `run.sh` and `start-clap-listener.sh`:

```bash
export DISPLAY="${DISPLAY:-:0}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export QT_QPA_PLATFORM=xcb
export XDG_DESKTOP_DIR=$HOME/Desktop
export XDG_DOWNLOAD_DIR=$HOME/Downloads
export XDG_DOCUMENTS_DIR=$HOME/Documents
export XDG_PICTURES_DIR=$HOME/Pictures
export XDG_MUSIC_DIR=$HOME/Music
export XDG_VIDEOS_DIR=$HOME/Videos
```

### System Prompt (`core/prompt.txt`)

Defines the assistant's personality, rules, and tool routing behavior. Edit this file to customize how JarvisPocho behaves.

---

## Usage

### Voice Commands

Just talk to JarvisPocho. Examples:

- *"Abrí Chrome"* — Opens Chrome
- *"Qué tiempo hace en San José?"* — Weather report
- *"Buscá recetas de gallo pinto"* — Web search
- *"Mandale un mensaje a María por WhatsApp"* — Send message
- *"Poné un recordatorio para mañana a las 8"* — Set reminder
- *"Qué ves en mi pantalla?"* — Screen vision
- *"Cerrá Spotify"* — Close specific window
- *"Escribí hola mundo"* — Type text
- *"Dale enter"* — Press Enter key

### Text Commands

Type directly in the UI text input field.

### File Upload

Drag and drop or click the file picker to upload files for processing.

### Clap Launch

Clap twice to launch JarvisPocho (when clap listener is running).

---

## Troubleshooting

### No audio output
```bash
# Check audio devices
pactl list short sinks
# Test audio
speaker-test -c 2
```

### Clap listener not detecting
```bash
# Test microphone
arecord -f S16_LE -r 16000 -d 3 test.wav && aplay test.wav

# Adjust sensitivity in clap_detector.py
threshold=0.4  # Lower = more sensitive
```

### Keyboard input not working on Wayland
```bash
# Ensure wtype is installed
pacman -Q wtype

# Test wtype
wtype "test"
```

### Window closing not working
```bash
# Test hyprctl
hyprctl clients -j
hyprctl dispatch killactive
```

### Port conflicts
```bash
ps aux | grep -E "python|sounddevice" | grep -v grep
pkill -9 -f "main.py"
```

### Memory issues
```bash
# View current memory
cat memory/long_term.json

# Reset memory
rm memory/long_term.json
```

---

## License

Personal and non-commercial use only.

Licensed under **[Creative Commons BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)**.

---

## Acknowledgments

Based on the [MARK XXXIX](https://github.com/FatihMakes/Mark-XXXIX) project by FatihMakes.
Personalized and enhanced for Arch Linux + Hyprland (Omarchy) with Costa Rican flair.
