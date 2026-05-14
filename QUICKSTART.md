# MARK XXXIX - Quick Start Guide

## Run JARVIS

```bash
cd ~/Projects/Mark-XXXIX
./run.sh
```

## Run with Clap Listener (2 claps to launch)

```bash
cd ~/Projects/Mark-XXXIX
./start-clap-listener.sh
```

Then clap twice to launch JARVIS.

## View Clap Listener Logs

```bash
tail -f /tmp/mark-xxxix-clap.log
```

## Kill All Processes

```bash
pkill -9 -f "clap" 2>/dev/null
pkill -9 -f "main.py" 2>/dev/null
```

## Project Location

```
~/Projects/Mark-XXXIX/
├── run.sh                  # Main launcher
├── start-clap-listener.sh   # Background clap listener
├── clap_listener_loop.sh   # Auto-restart loop
├── clap_detector.py        # Clap detection module
├── main.py                 # JARVIS entry point
├── ui.py                   # PyQt6 interface
├── CLAP_LISTENER.md        # Full clap listener docs
└── config/
    └── api_keys.json       # Gemini API key
```