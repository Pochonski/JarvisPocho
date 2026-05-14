#computer_control.py
import io
import json
import os
import re
import string
import subprocess
import sys
import time
import random
from pathlib import Path

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE    = 0.05
    _PYAUTOGUI = True
except ImportError:
    _PYAUTOGUI = False

try:
    import pyperclip
    _PYPERCLIP = True
except ImportError:
    _PYPERCLIP = False

def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


_BASE         = _base_dir()
_CONFIG_PATH  = _BASE / "config" / "api_keys.json"
_MEMORY_PATH  = _BASE / "memory" / "long_term.json"

def _load_config() -> dict:
    try:
        return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _get_os() -> str:
    return _load_config().get("os_system", "windows").lower()


def _get_api_key() -> str:
    return _load_config().get("gemini_api_key", "")

_SAFE_SCREENSHOT_ROOTS = (
    Path.home(),
)

def _safe_screenshot_path(requested: str | None) -> Path:
    fallback = Path.home() / "Desktop" / "jarvis_screenshot.png"
    if not requested:
        return fallback
    try:
        p = Path(requested).expanduser().resolve()
        for root in _SAFE_SCREENSHOT_ROOTS:
            if p.is_relative_to(root.resolve()):
                p.parent.mkdir(parents=True, exist_ok=True)
                return p
    except Exception:
        pass
    return fallback

def _require_pyautogui():
    if not _PYAUTOGUI:
        raise RuntimeError("PyAutoGUI not installed. Run: pip install pyautogui")

_FIRST_NAMES = [
    "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Drew", "Quinn",
    "Avery", "Blake", "Cameron", "Dakota", "Emerson", "Finley", "Harper",
]
_LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Wilson", "Moore", "Taylor", "Anderson", "Thomas", "Jackson",
]
_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "proton.me", "mail.com"]


def _random_data(data_type: str) -> str:
    dt = data_type.lower().strip()

    if dt == "first_name":
        return random.choice(_FIRST_NAMES)

    if dt == "last_name":
        return random.choice(_LAST_NAMES)

    if dt == "name":
        return f"{random.choice(_FIRST_NAMES)} {random.choice(_LAST_NAMES)}"

    if dt == "email":
        first = random.choice(_FIRST_NAMES).lower()
        last  = random.choice(_LAST_NAMES).lower()
        num   = random.randint(10, 999)
        return f"{first}.{last}{num}@{random.choice(_DOMAINS)}"

    if dt == "username":
        return f"{random.choice(_FIRST_NAMES).lower()}{random.randint(100, 9999)}"

    if dt == "password":
        chars = string.ascii_letters + string.digits + "!@#$%"
        raw   = (
            random.choice(string.ascii_uppercase)
            + random.choice(string.digits)
            + random.choice("!@#$%")
            + "".join(random.choices(chars, k=9))
        )
        return "".join(random.sample(raw, len(raw)))

    if dt == "phone":
        return f"+1{random.randint(200,999)}{random.randint(1_000_000, 9_999_999)}"

    if dt == "birthday":
        y = random.randint(1980, 2000)
        m = random.randint(1, 12)
        d = random.randint(1, 28)
        return f"{m:02d}/{d:02d}/{y}"

    if dt == "address":
        num    = random.randint(100, 9999)
        street = random.choice(["Main St", "Oak Ave", "Park Blvd", "Elm St", "Cedar Ln"])
        return f"{num} {street}"

    if dt == "zip_code":
        return str(random.randint(10000, 99999))

    if dt == "city":
        return random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"])

    return f"random_{data_type}_{random.randint(1000, 9999)}"

# Mapping of Omarchy key names to hyprctl key symbols
_HYPR_KEYS = {
    "return": "Return", "enter": "Return", "space": "Space",
    "tab": "Tab", "escape": "Escape", "backspace": "BackSpace",
    "delete": "Delete", "up": "Up", "down": "Down", "left": "Left", "right": "Right",
    "home": "Home", "end": "End", "pageup": "Page_Up", "pagedown": "Page_Down",
    "f1": "F1", "f2": "F2", "f3": "F3", "f4": "F4", "f5": "F5", "f6": "F6",
    "f7": "F7", "f8": "F8", "f9": "F9", "f10": "F10", "f11": "F11", "f12": "F12",
}

# Direct commands for SUPER+ shortcuts (bypass key simulation)
_HOTKEY_COMMANDS = {
    "SUPER+RETURN":     'uwsm-app -- xdg-terminal-exec --dir="$(omarchy-cmd-terminal-cwd)"',
    "SUPER+SHIFT+RETURN": 'omarchy-launch-browser',
    "SUPER+SHIFT+F":    'uwsm-app -- nautilus --new-window',
    "SUPER+SHIFT+V":    'code',
    "SUPER+SHIFT+B":    'omarchy-launch-browser',
    "SUPER+SHIFT+M":    'omarchy-launch-or-focus spotify',
    "SUPER+SHIFT+A":    'omarchy-launch-webapp "https://chatgpt.com"',
    "SUPER+SHIFT+Y":    'omarchy-launch-webapp "https://youtube.com/"',
    "SUPER+CTRL+V":      '~/.local/bin/cliphist-picker.sh',
    "SUPER+T":          'uwsm-app -- xdg-terminal-exec',  # toggle tiling
}

def _exec_hotkey_command(keys_str: str) -> str:
    """Ejecuta el comando directo asociado a un hotkey en background."""
    cmd = _HOTKEY_COMMANDS.get(keys_str.upper())
    if not cmd:
        return None
    try:
        subprocess.run(
            ["bash", "-c", f"{cmd} &>/dev/null &"],
            capture_output=True, timeout=3
        )
        return f"Executed: {keys_str}"
    except Exception as e:
        return f"Command failed: {e}"

def _hypr_key_name(key: str) -> str:
    return _HYPR_KEYS.get(key.lower().strip(), key)

def _exec_hypr_hotkey(modifier: str, key: str, extra: str = "") -> str:
    mod = modifier.upper()
    k = _hypr_key_name(key)
    cmd = f"bind={mod}{extra},{k}"
    try:
        subprocess.run(["hyprctl", "dispatch", cmd], capture_output=True, timeout=2)
        return f"Hypr key: {mod}+{key}"
    except Exception as e:
        return f"hyprctl failed: {e}"

# ydotool keycodes (linux/input-event-codes)
_YDOTOOL_KEYCODES = {
    # Modifiers
    "SUPER": 125, "META": 125, "WIN": 125, "LEFTMETA": 125, "RIGHTMETA": 126,
    "SHIFT": 42, "LEFTSHIFT": 42, "RIGHTSHIFT": 54,
    "CTRL": 29, "CONTROL": 29, "LEFTCTRL": 29, "RIGHTCTRL": 97,
    "ALT": 56, "LEFTALT": 56, "RIGHTALT": 100,
    "TAB": 15,
    # Letters
    "A": 30, "B": 48, "C": 46, "D": 32, "E": 18, "F": 33, "G": 34, "H": 35,
    "I": 23, "J": 36, "K": 37, "L": 38, "M": 50, "N": 49, "O": 24, "P": 25,
    "Q": 16, "R": 19, "S": 31, "T": 20, "U": 22, "V": 47, "W": 17, "X": 45,
    "Y": 21, "Z": 44,
    # Numbers
    "1": 2, "2": 3, "3": 4, "4": 5, "5": 6, "6": 7, "7": 8, "8": 9, "9": 10, "0": 11,
    # Navigation
    "RETURN": 28, "ENTER": 28, "ESCAPE": 1, "ESC": 1, "SPACE": 57,
    "BACKSPACE": 14, "DELETE": 111,
    "UP": 103, "DOWN": 108, "LEFT": 105, "RIGHT": 106,
    "HOME": 102, "END": 107, "PAGEUP": 104, "PAGEDOWN": 109,
    # Function keys
    "F1": 59, "F2": 60, "F3": 61, "F4": 62, "F5": 63, "F6": 64,
    "F7": 65, "F8": 66, "F9": 67, "F10": 68, "F11": 87, "F12": 88,
    # Symbols
    "MINUS": 12, "EQUAL": 13, "COMMA": 51, "PERIOD": 52, "SLASH": 53,
    "SEMICOLON": 39, "APOSTROPHE": 40, "GRAVE": 41,
    "LEFTBRACKET": 26, "RIGHTBRACKET": 27, "BACKSLASH": 43,
    "PRINT": 99, "SCROLLLOCK": 70, "PAUSE": 127,
    "INSERT": 110, "MENU": 127,
}

def _ydotool_hotkey(*keys) -> str:
    """Simula atajo de teclado usando ydotool"""
    import subprocess

    keycodes = []
    for k in keys:
        k_upper = k.upper()
        if k_upper in _YDOTOOL_KEYCODES:
            keycodes.append(_YDOTOOL_KEYCODES[k_upper])
        else:
            print(f"[ComputerControl] ⚠️ Unknown key: {k}")
            return f"Unknown key: {k}"

    # Build press+release sequence: KEY:1 down, KEY:0 up
    seq_parts = []
    for kc in keycodes:
        seq_parts.append(f"{kc}:1")
    for kc in reversed(keycodes):
        seq_parts.append(f"{kc}:0")

    seq = " ".join(seq_parts)

    try:
        env = os.environ.copy()
        env["YDOTOOL_SOCKET"] = "/run/user/1000/.ydotool_socket"
        env["XDG_RUNTIME_DIR"] = "/run/user/1000"
        env["WAYLAND_DISPLAY"] = "wayland-1"
        result = subprocess.run(
            ["ydotool", "key", seq],
            capture_output=True, timeout=2, env=env
        )
        if result.returncode != 0:
            return f"ydotool failed: {result.stderr.decode()[:100]}"
        return f"Hotkey: {'+'.join(keys)}"
    except Exception as e:
        return f"ydotool error: {e}"


def _ydotool_key(key: str) -> str:
    """Press and release a single key using ydotool."""
    return _ydotool_hotkey(key)


def _run_ydotool_script(*keys) -> str:
    """Escribe script sh temporal y lo ejecuta para simular hotkey"""
    import subprocess, tempfile, os

    keycodes = []
    for k in keys:
        k_upper = k.upper()
        if k_upper in _YDOTOOL_KEYCODES:
            keycodes.append(_YDOTOOL_KEYCODES[k_upper])
        else:
            print(f"[ComputerControl] ⚠️ Unknown key: {k}")
            return f"Unknown key: {k}"

    seq_parts = []
    for kc in keycodes:
        seq_parts.append(f"{kc}:1")
    for kc in reversed(keycodes):
        seq_parts.append(f"{kc}:0")
    seq = " ".join(seq_parts)

    script_content = f'''#!/bin/bash
export YDOTOOL_SOCKET=/run/user/1000/.ydotool_socket
export XDG_RUNTIME_DIR=/run/user/1000
export WAYLAND_DISPLAY=wayland-1
/usr/bin/ydotool key {seq}
'''

    fd, path = tempfile.mkstemp(suffix=".sh")
    os.write(fd, script_content.encode())
    os.close(fd)
    os.chmod(path, 0o755)

    try:
        result = subprocess.run(
            ["bash", path],
            capture_output=True, timeout=3
        )
        if result.returncode != 0:
            return f"script failed: {result.stderr.decode()[:100]}"
        return f"Hotkey: {'+'.join(keys)}"
    except Exception as e:
        return f"script error: {e}"
    finally:
        os.unlink(path)

def _user_profile() -> dict:
    """Read identity fields from long-term memory."""
    try:
        if _MEMORY_PATH.exists():
            data     = json.loads(_MEMORY_PATH.read_text(encoding="utf-8"))
            identity = data.get("identity", {})
            return {k: v.get("value", "") for k, v in identity.items()}
    except Exception:
        pass
    return {}

def _type(text: str, interval: float = 0.03) -> str:
    _require_pyautogui()
    time.sleep(0.3)
    pyautogui.typewrite(text, interval=interval)
    return f"Typed: {text[:60]}{'…' if len(text) > 60 else ''}"


def _smart_type(text: str, clear_first: bool = True) -> str:
    _require_pyautogui()
    if clear_first:
        _clear_field()
        time.sleep(0.1)

    if len(text) > 20 and _PYPERCLIP:
        pyperclip.copy(text)
        time.sleep(0.1)
        pyautogui.hotkey("ctrl", "v")
        return f"Smart-typed (clipboard): {text[:60]}{'…' if len(text) > 60 else ''}"

    pyautogui.typewrite(text, interval=0.04)
    return f"Smart-typed: {text[:60]}{'…' if len(text) > 60 else ''}"


def _click(x=None, y=None, button: str = "left", clicks: int = 1) -> str:
    _require_pyautogui()
    if x is not None and y is not None:
        pyautogui.click(x, y, button=button, clicks=clicks)
        return f"{'Double-c' if clicks == 2 else 'C'}licked ({x}, {y}) [{button}]"
    pyautogui.click(button=button, clicks=clicks)
    return f"Clicked at current position [{button}]"


def _hotkey(*keys) -> str:
    _require_pyautogui()
    pyautogui.hotkey(*keys)
    return f"Hotkey: {'+'.join(keys)}"


def _press(key: str) -> str:
    _require_pyautogui()
    pyautogui.press(key)
    return f"Pressed: {key}"


def _scroll(direction: str = "down", amount: int = 3) -> str:
    _require_pyautogui()
    vertical   = direction in ("up", "down")
    clicks     = amount if direction in ("up", "right") else -amount
    pyautogui.scroll(clicks) if vertical else pyautogui.hscroll(clicks)
    return f"Scrolled {direction} ×{amount}"


def _move(x: int, y: int, duration: float = 0.3) -> str:
    _require_pyautogui()
    pyautogui.moveTo(x, y, duration=duration)
    return f"Mouse → ({x}, {y})"


def _drag(x1: int, y1: int, x2: int, y2: int, duration: float = 0.5) -> str:
    _require_pyautogui()
    pyautogui.moveTo(x1, y1, duration=0.2)
    pyautogui.dragTo(x2, y2, duration=duration, button="left")
    return f"Dragged ({x1},{y1}) → ({x2},{y2})"


def _clipboard_get() -> str:
    try:
        result = subprocess.run(["wl-paste"], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            return result.stdout.strip()
        return f"wl-paste failed: {result.stderr}"
    except Exception as e:
        return f"wl-paste error: {e}"


def _clipboard_paste(text: str) -> str:
    try:
        subprocess.run(["wl-copy"], input=text, text=True, capture_output=True, timeout=2)
        time.sleep(0.1)
        _require_pyautogui()
        pyautogui.hotkey("winleft", "v")
        return f"Pasted: {text[:60]}{'…' if len(text) > 60 else ''}"
    except Exception as e:
        return f"wl-copy failed: {e}"


def _screenshot(save_path: str | None = None) -> str:
    _require_pyautogui()
    path = _safe_screenshot_path(save_path)
    img  = pyautogui.screenshot()
    img.save(str(path))
    return f"Screenshot saved: {path}"


def _clear_field() -> str:
    _require_pyautogui()
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.1)
    pyautogui.press("delete")
    return "Field cleared"

def _focus_window(title: str) -> str:
    os_name = _get_os()

    if os_name == "windows":
        try:
            script = f'(New-Object -ComObject WScript.Shell).AppActivate("{title}")'
            subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                capture_output=True, timeout=5,
            )
            time.sleep(0.3)
            return f"Focused window: {title}"
        except Exception as e:
            return f"focus_window (Windows) failed: {e}"

    if os_name == "mac":
        script = (
            f'tell application "System Events" to '
            f'set frontmost of (first process whose name contains "{title}") to true'
        )
        try:
            subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, timeout=5,
            )
            time.sleep(0.3)
            return f"Focused window: {title}"
        except Exception as e:
            return f"focus_window (macOS) failed: {e}"

    if os_name == "linux":
        try:
            result = subprocess.run(
                ["wmctrl", "-a", title],
                capture_output=True, timeout=5,
            )
            if result.returncode == 0:
                time.sleep(0.3)
                return f"Focused window: {title}"
        except FileNotFoundError:
            pass
        try:
            result = subprocess.run(
                ["xdotool", "search", "--name", title, "windowactivate"],
                capture_output=True, timeout=5,
            )
            time.sleep(0.3)
            return f"Focused window: {title}"
        except FileNotFoundError:
            return "focus_window (Linux) requires wmctrl or xdotool"
        except Exception as e:
            return f"focus_window (Linux) failed: {e}"

    return f"focus_window: unknown OS '{os_name}'"

def _screen_find(description: str) -> tuple[int, int] | None:
    api_key = _get_api_key()
    if not api_key:
        print("[ComputerControl] ⚠️ No API key for screen_find")
        return None

    try:
        from google import genai
        from google.genai import types as gtypes

        _require_pyautogui()
        w, h  = pyautogui.size()
        img   = pyautogui.screenshot()
        buf   = io.BytesIO()
        img.save(buf, format="PNG")
        image_bytes = buf.getvalue()

        client = genai.Client(api_key=api_key)
        prompt = (
            f"This is a screenshot of a {w}×{h} pixel screen. "
            f"Locate the UI element described as: '{description}'. "
            f"Reply with ONLY the center coordinates as: x,y "
            f"If the element is not visible, reply: NOT_FOUND"
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[
                gtypes.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                prompt,
            ],
        )

        text = (response.text or "").strip()
        if "NOT_FOUND" in text.upper():
            return None

        match = re.search(r"(\d+)\s*,\s*(\d+)", text)
        if match:
            return int(match.group(1)), int(match.group(2))

    except Exception as e:
        print(f"[ComputerControl] ⚠️ screen_find failed: {e}")

    return None

def computer_control(
    parameters: dict,
    response=None,
    player=None,
    session_memory=None,
) -> str:
    """
    Dispatch table for all computer control actions.

    parameters keys (all optional unless noted):
      action        : (required) one of the actions listed below
      text          : text to type or paste
      x, y          : screen coordinates
      button        : 'left' | 'right' (default: left)
      keys          : hotkey string, e.g. 'ctrl+c'
      key           : single key name, e.g. 'enter'
      direction     : 'up' | 'down' | 'left' | 'right'
      amount        : scroll amount (default: 3)
      seconds       : wait duration
      title         : window title fragment for focus_window
      description   : natural-language element description for screen_find/click
      type          : data type for random_data
      field         : memory field name for user_data
      clear_first   : bool, clear field before typing (default: true)
      path          : save path for screenshot (must be inside home dir)

    Actions:
      type          — type text at cursor
      smart_type    — clear field + type (clipboard-backed)
      click         — left click
      double_click  — double left click
      right_click   — right click
      move          — move mouse
      drag          — click-drag between two points
      hotkey        — key combination
      press         — single key
      scroll        — scroll the wheel
      copy          — read clipboard
      paste         — write + paste clipboard
      screenshot    — capture screen (safe path only)
      wait          — sleep N seconds
      clear_field   — select-all + delete
      focus_window  — bring window to foreground
      screen_find   — AI element finder (returns x,y)
      screen_click  — AI element finder + click
      random_data   — generate fake form data
      user_data     — pull real data from memory
    """
    params = parameters or {}
    action = params.get("action", "").lower().strip()

    if not action:
        return "No action specified for computer_control."

    if player:
        player.write_log(f"[Computer] {action}")

    print(f"[ComputerControl] ▶ {action}  {params}")

    try:

        if action == "type":
            return _type(params.get("text", ""))

        if action == "smart_type":
            return _smart_type(
                params.get("text", ""),
                clear_first=params.get("clear_first", True),
            )

        if action in ("click", "left_click"):
            return _click(params.get("x"), params.get("y"), "left", 1)

        if action == "double_click":
            return _click(params.get("x"), params.get("y"), "left", 2)

        if action == "right_click":
            return _click(params.get("x"), params.get("y"), "right", 1)

        if action == "move":
            return _move(int(params.get("x", 0)), int(params.get("y", 0)))

        if action == "drag":
            return _drag(
                int(params.get("x1", 0)), int(params.get("y1", 0)),
                int(params.get("x2", 0)), int(params.get("y2", 0)),
            )

        if action == "hotkey":
                raw  = params.get("keys", "")
                keys = [k.strip() for k in raw.split("+")] if isinstance(raw, str) else raw

                def _parse_num(k):
                    k = k.lower()
                    if k in ("1", "code:10"): return 1
                    if k in ("2", "code:11"): return 2
                    if k in ("3", "code:12"): return 3
                    if k in ("4", "code:13"): return 4
                    if k in ("5", "code:14"): return 5
                    if k in ("6", "code:15"): return 6
                    if k in ("7", "code:16"): return 7
                    if k in ("8", "code:17"): return 8
                    if k in ("9", "code:18"): return 9
                    if k in ("0", "code:19"): return 10
                    return None

                # SUPER+[1-0] = switch workspace
                if len(keys) == 2 and keys[0].upper() in ("SUPER", "WIN", "META"):
                    num = _parse_num(keys[1])
                    if num:
                        try:
                            subprocess.run(
                                ["hyprctl", "dispatch", f"workspace {num}"],
                                capture_output=True, timeout=2
                            )
                            return f"Workspace: {num}"
                        except Exception as e:
                            return f"hyprctl workspace failed: {e}"

                # SUPER+SHIFT+[1-0] = move window to workspace
                if len(keys) == 3 and keys[0].upper() in ("SUPER", "WIN", "META") and keys[1].upper() == "SHIFT":
                    num = _parse_num(keys[2])
                    if num:
                        try:
                            subprocess.run(
                                ["hyprctl", "dispatch", f"movetoworkspace {num}"],
                                capture_output=True, timeout=2
                            )
                            return f"Window moved to workspace {num}"
                        except Exception as e:
                            return f"hyprctl movetoworkspace failed: {e}"

                # All SUPER+ combos → try direct command first, then ydotool fallback
                keys_str = "+".join(k.upper() for k in keys)
                result = _exec_hotkey_command(keys_str)
                if result:
                    return result
                return _run_ydotool_script(*keys)

                # Non-SUPER hotkeys (Ctrl+C, Ctrl+V, etc.) → use ydotool via script
                return _run_ydotool_script(*keys)

        if action == "press":
            return _ydotool_key(params.get("key", "enter"))

        if action == "scroll":
            return _scroll(
                direction=params.get("direction", "down"),
                amount=int(params.get("amount", 3)),
            )

        if action == "copy":
            return _clipboard_get()

        if action == "paste":
            return _clipboard_paste(params.get("text", ""))

        if action == "screenshot":
            return _screenshot(params.get("path"))

        if action == "screen_find":
            coords = _screen_find(params.get("description", ""))
            return f"{coords[0]},{coords[1]}" if coords else "NOT_FOUND"

        if action == "screen_click":
            desc   = params.get("description", "")
            coords = _screen_find(desc)
            if coords:
                time.sleep(0.2)
                _click(x=coords[0], y=coords[1])
                return f"Clicked '{desc}' at {coords}"
            return f"Element not found on screen: '{desc}'"

        if action == "wait":
            secs = float(params.get("seconds", 1.0))
            secs = min(secs, 30.0)
            time.sleep(secs)
            return f"Waited {secs}s"

        if action == "clear_field":
            return _clear_field()

        if action == "focus_window":
            return _focus_window(params.get("title", ""))

        if action == "random_data":
            dt     = params.get("type", "name")
            result = _random_data(dt)
            print(f"[ComputerControl] 🎲 random {dt} → {result}")
            return result

        if action == "user_data":
            field   = params.get("field", "name")
            profile = _user_profile()
            value   = profile.get(field, "")
            if not value:
                value = _random_data(field)
                print(f"[ComputerControl] ⚠️ No '{field}' in memory, using random: {value}")
            return value

        return f"Unknown action: '{action}'"

    except Exception as e:
        print(f"[ComputerControl] ❌ {action}: {e}")
        return f"computer_control '{action}' failed: {e}"