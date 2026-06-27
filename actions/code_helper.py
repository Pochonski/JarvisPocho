import subprocess
import sys
import json
import re
import time
from pathlib import Path

from providers import generate as opencode_generate


def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR           = get_base_dir()
API_CONFIG_PATH    = BASE_DIR / "config" / "api_keys.json"
DESKTOP            = Path.home() / "Desktop"
MAX_BUILD_ATTEMPTS = 3


def _get_api_key() -> str:
    with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["gemini_api_key"]


def _clean_code(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


def _resolve_save_path(output_path: str, language: str) -> Path:
    ext_map = {
        "python": ".py", "py": ".py",
        "javascript": ".js", "js": ".js",
        "typescript": ".ts", "ts": ".ts",
        "html": ".html", "css": ".css",
        "java": ".java", "cpp": ".cpp", "c": ".c",
        "bash": ".sh", "shell": ".sh", "powershell": ".ps1",
        "sql": ".sql", "json": ".json", "rust": ".rs", "go": ".go",
    }
    if output_path:
        p = Path(output_path)
        return p if p.is_absolute() else DESKTOP / p
    ext = ext_map.get((language or "python").lower(), ".py")
    return DESKTOP / f"jarvis_code{ext}"


def _read_file(file_path: str) -> tuple[str, str]:
    if not file_path:
        return "", "No file path provided."
    p = Path(file_path)
    if not p.exists():
        return "", f"File not found: {file_path}"
    try:
        return p.read_text(encoding="utf-8"), ""
    except Exception as e:
        return "", f"Could not read file: {e}"


def _save_file(path: Path, content: str) -> str:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"Saved to: {path}"
    except Exception as e:
        return f"Could not save: {e}"


def _preview(code: str, lines: int = 10) -> str:
    all_lines = code.splitlines()
    preview   = "\n".join(all_lines[:lines])
    suffix    = f"\n... ({len(all_lines) - lines} more lines)" if len(all_lines) > lines else ""
    return preview + suffix


def _has_error(output: str) -> bool:
    error_signals = ["error", "exception", "traceback", "syntaxerror",
                     "nameerror", "typeerror", "stderr", "failed", "crash"]
    return any(s in output.lower() for s in error_signals)


def _take_screenshot() -> Path | None:
    try:
        import pyautogui
        screenshot_path = Path.home() / "Desktop" / f"jarvis_debug_{int(time.time())}.png"
        screenshot = pyautogui.screenshot()
        screenshot.save(str(screenshot_path))
        print(f"[Code] 📸 Screenshot: {screenshot_path}")
        return screenshot_path
    except Exception as e:
        print(f"[Code] ⚠️ Screenshot failed: {e}")
        return None


def _image_to_base64(path: Path) -> str:
    import base64
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def _detect_intent(description: str, file_path: str, code: str) -> str:
    desc = (description or "").lower()

    screen_kw = ["ekrandaki", "screen", "ekranda", "bu hatayı", "why am i getting",
                 "neden hata", "what's wrong", "ne yanlış", "screenshot", "görüntü"]
    if any(k in desc for k in screen_kw):
        return "screen_debug"

    optimize_kw = ["optimize", "refactor", "clean up", "improve", "temizle",
                   "iyileştir", "daha iyi", "make it better", "hızlandır"]
    if any(k in desc for k in optimize_kw) and (code or file_path):
        return "optimize"

    if file_path:
        p = Path(file_path)
        edit_kw  = ["edit", "update", "modify", "change", "add", "remove",
                    "refactor", "fix", "rename", "replace", "düzenle", "değiştir"]
        run_kw   = ["run", "execute", "launch", "start", "çalıştır"]
        build_kw = ["build", "make it work", "try", "attempt"]

        if p.exists() and any(k in desc for k in edit_kw):
            return "edit"
        if p.exists() and any(k in desc for k in run_kw):
            return "run"
        if any(k in desc for k in build_kw):
            return "build"
        if p.exists():
            return "explain"

    explain_kw = ["explain", "what does", "describe", "analyze", "açıkla", "ne yapıyor"]
    if any(k in desc for k in explain_kw) and (code or file_path):
        return "explain"

    build_kw = ["build", "make it work", "try and", "attempt"]
    if any(k in desc for k in build_kw):
        return "build"

    return "write"

def _write(description: str, language: str, output_path: str, player=None) -> tuple[str, Path]:
    lang  = language or "python"

    prompt = f"""You are an expert {lang} developer.
Write clean, working, well-commented {lang} code for the description below.

Rules:
- Output ONLY the code. No explanation, no markdown, no backticks.
- Add helpful inline comments.
- Handle errors and edge cases properly.
- Use modern best practices.

Description: {description}

Code:"""

    response = opencode_generate(prompt)
    code     = _clean_code(response)
    path     = _resolve_save_path(output_path, lang)
    _save_file(path, code)
    return code, path


def _fix_code(code: str, error_output: str, description: str) -> str:
    prompt = f"""You are an expert debugger.
The code below failed with the following error. Fix it.
Return ONLY the corrected code — no explanation, no markdown, no backticks.

Original goal: {description}

Error:
{error_output[:2000]}

Broken code:
{code}

Fixed code:"""

    response = opencode_generate(prompt)
    return _clean_code(response)


def _run_file(path: Path, args: list, timeout: int) -> str:
    interpreters = {
        ".py":  [sys.executable],
        ".js":  ["node"],
        ".ts":  ["ts-node"],
        ".sh":  ["bash"],
        ".ps1": ["powershell", "-File"],
        ".rb":  ["ruby"],
        ".php": ["php"],
    }
    suffix = path.suffix.lower()
    interp = interpreters.get(suffix)
    if not interp:
        return f"No interpreter for file type '{suffix or '(no extension)'}'. Supported: {', '.join(interpreters.keys())}. Use run_project for complete projects."

    try:
        result = subprocess.run(
            interp + [str(path)] + (args or []),
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=timeout, cwd=str(path.parent)
        )
        output = result.stdout.strip()
        error  = result.stderr.strip()
        parts  = []
        if output: parts.append(f"Output:\n{output}")
        if error:  parts.append(f"Stderr:\n{error}")
        return "\n\n".join(parts) if parts else "Executed with no output."

    except subprocess.TimeoutExpired:
        return f"Timed out after {timeout}s."
    except FileNotFoundError:
        return f"Interpreter not found: {interp[0]}."
    except Exception as e:
        return f"Execution error: {e}"


def _build(description, language, output_path, args, timeout, speak=None, player=None) -> str:
    if not description:
        return "Please describe what you want me to build, jefe."

    if player:
        player.write_log("[Code] Build started...")

    lang = language or "python"

    try:
        code, path = _write(description, lang, output_path, player)
        print(f"[Code] ✅ Written: {path}")
    except Exception as e:
        msg = f"Could not write initial code: {e}"
        if speak: speak(msg)
        return msg

    last_output = ""
    for attempt in range(1, MAX_BUILD_ATTEMPTS + 1):
        print(f"[Code] 🔄 Attempt {attempt}/{MAX_BUILD_ATTEMPTS}")
        if player:
            player.write_log(f"[Code] Attempt {attempt}...")

        last_output = _run_file(path, args, timeout)

        if not _has_error(last_output):
            msg = (
                f"Build complete, jefe. "
                f"The code is working after {attempt} attempt{'s' if attempt > 1 else ''}. "
                f"Saved to {path}."
            )
            if speak: speak(msg)
            return f"{msg}\n\nOutput:\n{last_output}"

        print(f"[Code] ⚠️ Error on attempt {attempt}, fixing...")
        if player:
            player.write_log(f"[Code] Fixing (attempt {attempt})...")

        try:
            code = _fix_code(code, last_output, description)
            _save_file(path, code)
        except Exception as e:
            msg = f"Could not fix code on attempt {attempt}: {e}"
            if speak: speak(msg)
            return msg

    msg = (
        f"I was unable to build a working version after {MAX_BUILD_ATTEMPTS} attempts, jefe. "
        f"The last error was: {last_output[:200]}"
    )
    if speak: speak(msg)
    return f"{msg}\n\nLast code saved to: {path}"

def _write_action(description, language, output_path, player) -> str:
    if not description:
        return "Please describe what you want me to write, jefe."
    if player:
        player.write_log("[Code] Writing code...")
    try:
        code, path = _write(description, language, output_path, player)
        print(f"[Code] ✅ Written: {path}")
        return f"Code written. Saved to: {path}\n\nPreview:\n{_preview(code)}"
    except Exception as e:
        return f"Could not generate code: {e}"


def _edit_action(file_path, instruction, player) -> str:
    if not file_path:
        return "Please provide a file path to edit, jefe."
    if not instruction:
        return "Please describe what change to make, jefe."

    content, err = _read_file(file_path)
    if err:
        return err

    if player:
        player.write_log("[Code] Editing file...")

    prompt = f"""You are an expert code editor.
Apply the following change to the code below.
Return ONLY the complete updated code — no explanation, no markdown, no backticks.

Change: {instruction}

Original code:
{content}

Updated code:"""

    try:
        response = opencode_generate(prompt)
        edited   = _clean_code(response)
    except Exception as e:
        return f"Could not edit code: {e}"

    status = _save_file(Path(file_path), edited)
    print(f"[Code] ✅ Edited: {file_path}")
    return f"File edited. {status}\n\nPreview:\n{_preview(edited)}"


def _explain_action(file_path, code, player) -> str:
    if file_path and not code:
        code, err = _read_file(file_path)
        if err:
            return err
    if not code:
        return "Please provide code or a file path to explain, jefe."

    if player:
        player.write_log("[Code] Analyzing code...")

    prompt = f"""Explain what this code does in simple, clear language.
Focus on: what it does, how it works, and any important details.
Be concise — 3 to 6 sentences maximum.

Code:
{code[:4000]}

Explanation:"""

    try:
        response = opencode_generate(prompt)
        return response.strip()
    except Exception as e:
        return f"Could not explain code: {e}"


def _run_action(file_path, args, timeout, player) -> str:
    if not file_path:
        return "Please provide a file path to run, jefe."
    p = Path(file_path).expanduser()

    # If it's a directory, redirect to run_project
    if p.is_dir():
        print(f"[Code] 📂 Path is a directory, redirecting to run_project")
        return _run_project_action(str(p), timeout, True, player)

    if not p.exists():
        return f"File not found: {file_path}"
    if player:
        player.write_log(f"[Code] Running {p.name}...")
    return _run_file(p, args, timeout)


def _optimize_action(file_path, code, language, output_path, player) -> str:

    if file_path and not code:
        code, err = _read_file(file_path)
        if err:
            return err
    if not code:
        return "Please provide code or a file path to optimize, jefe."

    if player:
        player.write_log("[Code] Optimizing code...")

    lang  = language or "python"

    prompt = f"""You are an expert {lang} developer and code reviewer.
Optimize the following code for:
1. Performance — eliminate unnecessary operations, use efficient data structures
2. Readability — clear variable names, proper formatting, logical structure
3. Best practices — modern {lang} patterns, error handling, type hints if applicable
4. Remove dead code, redundant comments, and unnecessary complexity

Return ONLY the optimized code — no explanation, no markdown, no backticks.

Original code:
{code[:6000]}

Optimized code:"""

    try:
        response  = opencode_generate(prompt)
        optimized = _clean_code(response)
    except Exception as e:
        return f"Could not optimize code: {e}"

    # Kaydet
    if file_path:
        save_path = Path(file_path)
    else:
        save_path = _resolve_save_path(output_path, lang)

    status = _save_file(save_path, optimized)
    print(f"[Code] ✅ Optimized: {save_path}")

    original_lines  = len(code.splitlines())
    optimized_lines = len(optimized.splitlines())
    diff = original_lines - optimized_lines

    return (
        f"Code optimized. {status}\n"
        f"Lines: {original_lines} → {optimized_lines} "
        f"({'−' if diff > 0 else '+'}{abs(diff)} lines)\n\n"
        f"Preview:\n{_preview(optimized)}"
    )


def _screen_debug_action(description, file_path, player, speak=None) -> str:

    if player:
        player.write_log("[Code] Taking screenshot for analysis...")

    print("[Code] 📸 Capturing screen for debug...")


    screenshot_path = _take_screenshot()
    if not screenshot_path:
        return "Could not take screenshot, jefe. Please make sure PyAutoGUI is installed."


    file_content = ""
    if file_path:
        file_content, err = _read_file(file_path)
        if err:
            print(f"[Code] ⚠️ Could not read file: {err}")

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=_get_api_key())

        image_bytes  = screenshot_path.read_bytes()
        image_base64 = _image_to_base64(screenshot_path)

        user_question = description or "What error or problem do you see on the screen? How can it be fixed?"

        context = ""
        if file_content:
            context = f"\n\nAdditionally, here is the related file content:\n```\n{file_content[:4000]}\n```"

        analysis_prompt = f"""You are an expert programmer and debugger analyzing a screenshot.

User's question: {user_question}{context}

Please:
1. Identify any errors, exceptions, or problems visible on the screen
2. Explain what is causing the problem in simple terms
3. Provide a concrete fix or solution
4. If there's code visible, show the corrected version

Be specific and actionable. If you see an error message, quote it exactly."""

        contents = [
            types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
            analysis_prompt,
        ]

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
        )

        analysis = response.text.strip()
        print(f"[Code] ✅ Screen analysis complete")

        try:
            screenshot_path.unlink()
        except Exception:
            pass

        if file_path and file_content:

            code_match = re.search(r"```[a-zA-Z]*\n(.*?)```", analysis, re.DOTALL)
            if code_match:
                fixed_code = code_match.group(1).strip()
                save_path  = Path(file_path)
                _save_file(save_path, fixed_code)
                analysis += f"\n\n✅ Fixed code has been saved to: {file_path}"
                print(f"[Code] ✅ Fixed code saved: {file_path}")

        return analysis

    except Exception as e:

        try:
            screenshot_path.unlink()
        except Exception:
            pass
        return f"Screen analysis failed: {e}"


_DANGEROUS_COMMANDS = [
    "git clone", "git init", "git fetch",
    "rm -rf", "rm -r", "rm -f",
    "sudo", "chmod", "chown",
    "mkfs", "dd if=", "fdisk",
    "curl | sh", "curl | bash", "wget | sh", "wget | bash",
    "> /dev/", "dd of=",
]

def _is_safe_command(cmd: str) -> bool:
    """Check if a command is safe to run (not destructive or repo-related)."""
    cmd_lower = cmd.lower().strip()
    for dangerous in _DANGEROUS_COMMANDS:
        if dangerous in cmd_lower:
            return False
    return True

def _detect_project_type(path: Path) -> dict:
    result = {
        "type": "unknown",
        "entry_point": None,
        "install_cmd": None,
        "run_cmd": None,
        "package_manager": None,
    }

    if not path.is_dir():
        return result

    children = {f.name for f in path.iterdir()}

    # Node.js
    if "package.json" in children:
        result["type"] = "node"
        result["install_cmd"] = "npm install"
        result["package_manager"] = "npm"
        if "pnpm-lock.yaml" in children or "pnpm-workspace.yaml" in children:
            result["package_manager"] = "pnpm"
            result["install_cmd"] = "pnpm install"
        elif "yarn.lock" in children:
            result["package_manager"] = "yarn"
            result["install_cmd"] = "yarn install"
        # Try to find entry point from package.json
        try:
            pkg = json.loads((path / "package.json").read_text())
            scripts = pkg.get("scripts", {})
            if "start" in scripts:
                result["run_cmd"] = f"{result['package_manager']} start"
            elif "dev" in scripts:
                result["run_cmd"] = f"{result['package_manager']} run dev"
            result["entry_point"] = pkg.get("main", None)
        except Exception:
            pass

    # Python
    elif "requirements.txt" in children or "pyproject.toml" in children or "Pipfile" in children:
        result["type"] = "python"
        if "requirements.txt" in children:
            result["install_cmd"] = "pip install -r requirements.txt"
        elif "pyproject.toml" in children:
            result["install_cmd"] = "pip install ."
        elif "Pipfile" in children:
            result["install_cmd"] = "pipenv install"
        # Find entry point
        for candidate in ["main.py", "app.py", "__main__.py", "manage.py", "server.py", "cli.py"]:
            if candidate in children:
                result["entry_point"] = candidate
                result["run_cmd"] = f"python {candidate}"
                break
        if "setup.py" in children and not result["run_cmd"]:
            result["run_cmd"] = "python setup.py run"
        if "pyproject.toml" in children and not result["run_cmd"]:
            result["run_cmd"] = "python -m ."

    # Rust
    elif "Cargo.toml" in children:
        result["type"] = "rust"
        result["install_cmd"] = "cargo build"
        result["run_cmd"] = "cargo run"
        result["entry_point"] = "src/main.rs"

    # Go
    elif "go.mod" in children:
        result["type"] = "go"
        result["install_cmd"] = "go mod download"
        result["run_cmd"] = "go run ."
        result["entry_point"] = "main.go"

    # Ruby
    elif "Gemfile" in children:
        result["type"] = "ruby"
        result["install_cmd"] = "bundle install"
        result["run_cmd"] = "bundle exec ruby main.rb"
        result["entry_point"] = "main.rb"

    # Java Maven
    elif "pom.xml" in children:
        result["type"] = "java_maven"
        result["install_cmd"] = "mvn dependency:resolve"
        result["run_cmd"] = "mvn exec:java"
        result["entry_point"] = "pom.xml"

    # Java Gradle
    elif "build.gradle" in children or "build.gradle.kts" in children:
        result["type"] = "java_gradle"
        result["install_cmd"] = "gradle dependencies"
        result["run_cmd"] = "gradle run"
        result["entry_point"] = "build.gradle"

    # Makefile
    elif "Makefile" in children or "makefile" in children:
        result["type"] = "make"
        result["install_cmd"] = "make"
        result["run_cmd"] = "make run"
        result["entry_point"] = "Makefile"

    # .NET
    elif any(f.endswith(".csproj") or f.endswith(".sln") for f in children):
        result["type"] = "dotnet"
        csproj = next((f for f in children if f.endswith(".csproj")), None)
        result["install_cmd"] = "dotnet restore"
        result["run_cmd"] = f"dotnet run"
        result["entry_point"] = csproj

    return result


def _read_run_instructions(path: Path) -> str | None:
    """Read README or similar files to find run instructions."""
    readme_names = ["README.md", "README.txt", "RUNNING.md", "CONTRIBUTING.md", "DEVELOPMENT.md"]
    content = None
    for name in readme_names:
        readme = path / name
        if readme.exists():
            try:
                content = readme.read_text(encoding="utf-8", errors="ignore")
                break
            except Exception:
                continue

    if not content:
        return None

    # Extract relevant sections
    sections = ["run", "usage", "getting started", "development", "quick start", "install", "build"]
    lines = content.split("\n")
    relevant_lines = []
    in_section = False
    in_code_block = False

    for line in lines:
        stripped = line.strip().lower()
        # Detect section headers (## Run, ### Usage, etc.)
        if stripped.startswith("#"):
            header_text = stripped.lstrip("# ").strip()
            in_section = any(s in header_text for s in sections)

        if in_section:
            relevant_lines.append(line)
            # Collect code blocks within sections
            if "```" in stripped:
                in_code_block = not in_code_block

    if not relevant_lines:
        # Fallback: extract all bash/sh code blocks
        in_block = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```bash") or stripped.startswith("```sh") or stripped.startswith("```"):
                in_block = not in_block
                continue
            if in_block:
                relevant_lines.append(line)

    if not relevant_lines:
        return None

    return "\n".join(relevant_lines[:50])  # Limit to avoid huge strings


def _install_deps(path: Path, project_type: str, pkg_manager: str = None, timeout: int = 120) -> str:
    """Install project dependencies based on project type."""
    install_cmds = {
        "node": {
            "npm": "npm install",
            "yarn": "yarn install",
            "pnpm": "pnpm install",
        },
        "python": "pip install -r requirements.txt",
        "rust": "cargo build",
        "go": "go mod download",
        "ruby": "bundle install",
        "java_maven": "mvn dependency:resolve",
        "java_gradle": "gradle dependencies",
        "dotnet": "dotnet restore",
        "make": "make",
    }

    if project_type == "node" and pkg_manager:
        cmd = install_cmds.get("node", {}).get(pkg_manager, "npm install")
    else:
        cmd = install_cmds.get(project_type)

    if not cmd:
        return "No install command known for this project type."

    # Safety check
    if not _is_safe_command(cmd):
        return f"Install command rejected as unsafe: {cmd}"

    # For Python with requirements.txt, check file exists
    if project_type == "python" and "requirements.txt" in cmd:
        if not (path / "requirements.txt").exists():
            if (path / "setup.py").exists():
                cmd = "pip install ."
            elif (path / "pyproject.toml").exists():
                cmd = "pip install ."
            else:
                return "No requirements.txt or setup.py found, skipping install."

    print(f"[Code] 📦 Installing deps: {cmd}")
    try:
        result = subprocess.run(
            cmd, shell=True,
            capture_output=True, text=True,
            timeout=timeout, cwd=str(path)
        )
        if result.returncode == 0:
            return f"Dependencies installed: {cmd}"
        error = result.stderr.strip()[:300]
        return f"Install failed: {error}"
    except subprocess.TimeoutExpired:
        return f"Install timed out after {timeout}s."
    except FileNotFoundError:
        return f"Command not found: {cmd.split()[0]}. Is it installed?"
    except Exception as e:
        return f"Install error: {e}"


def _find_run_command(path: Path, project_type: str, readme_hints: str = None) -> str:
    """Determine the best command to run the project."""
    # Priority 1: Use README hints if they contain commands
    if readme_hints:
        import re
        # Look for commands in code blocks
        code_blocks = re.findall(r"```(?:bash|sh)?\n(.*?)```", readme_hints, re.DOTALL)
        for block in code_blocks:
            lines = block.strip().split("\n")
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("echo"):
                    # Skip dangerous commands (git clone, rm -rf, etc.)
                    if _is_safe_command(line):
                        return line

    # Priority 2: Use detected run command
    detected = _detect_project_type(path)
    if detected.get("run_cmd"):
        return detected["run_cmd"]

    # Priority 3: Fallback heuristics
    children = {f.name for f in path.iterdir()}

    if project_type == "node":
        if "package.json" in children:
            try:
                pkg = json.loads((path / "package.json").read_text())
                scripts = pkg.get("scripts", {})
                if "start" in scripts:
                    return "npm start"
                if "dev" in scripts:
                    return "npm run dev"
            except Exception:
                pass
        # Try to find entry file
        for candidate in ["index.js", "index.ts", "server.js", "app.js", "main.js"]:
            if candidate in children:
                return f"node {candidate}"

    elif project_type == "python":
        for candidate in ["main.py", "app.py", "__main__.py", "manage.py", "server.py"]:
            if candidate in children:
                return f"python {candidate}"

    elif project_type == "rust":
        return "cargo run"

    elif project_type == "go":
        return "go run ."

    return None


def _detect_web_server(output: str) -> int | None:
    """Detect if output indicates a web server is running and extract port."""
    patterns = [
        r"[Ll]isten(?:ing)? on port (\d+)",
        r"[Ss]erver running.*?port (\d+)",
        r"[Ss]tarted.*?http://[^\s:]+:(\d+)",
        r"http://localhost:(\d+)",
        r"http://127\.0\.0\.1:(\d+)",
        r"[Ll]ocal:\s+http://[^\s]+:(\d+)",
        r"webpack.*?compiled.*?http://[^\s]+:(\d+)",
        r"vite.*?http://[^\s]+:(\d+)",
        r"next.*?http://[^\s]+:(\d+)",
        r"react.*?http://[^\s]+:(\d+)",
    ]
    import re
    for pattern in patterns:
        match = re.search(pattern, output)
        if match:
            return int(match.group(1))

    # Fallback: check common ports in output
    for port in [3000, 8080, 8000, 5000, 5173, 4200, 9000, 8081, 3001]:
        if str(port) in output:
            return port

    return None


def _run_project_action(project_path: str, timeout: int = 60, open_browser: bool = True, player=None) -> str:
    """Run a complete project: detect type, install deps, execute, detect web server."""
    path = Path(project_path).expanduser()

    # Handle shortcuts: "projects/..." -> ~/Projects/...
    if not path.is_absolute():
        lower = path.parts[0].lower() if path.parts else ""
        if lower in ("projects", "project"):
            path = Path.home() / "Projects" / Path(*path.parts[1:])
        else:
            path = Path.home() / path

    path = path.resolve()

    if not path.exists():
        return f"Project path not found: {project_path}"
    if not path.is_dir():
        return f"Project path is not a directory: {project_path}"

    if player:
        player.write_log(f"[Code] Running project: {path.name}")

    # Step 1: Detect project type
    project_info = _detect_project_type(path)
    project_type = project_info["type"]

    if project_type == "unknown":
        return f"Could not detect project type for: {path.name}. Supported: Node.js, Python, Rust, Go, Ruby, Java, Makefile, .NET"

    print(f"[Code] 📂 Project type: {project_type} at {path}")

    # Step 2: Read README for run instructions
    readme_hints = _read_run_instructions(path)
    if readme_hints:
        print(f"[Code] 📖 Found README hints ({len(readme_hints)} chars)")

    # Step 3: Install dependencies
    install_result = _install_deps(
        path, project_type,
        pkg_manager=project_info.get("package_manager"),
        timeout=120
    )
    print(f"[Code] 📦 Install: {install_result[:100]}")

    # Step 4: Find run command
    run_cmd = _find_run_command(path, project_type, readme_hints)
    if not run_cmd:
        return f"Could not determine how to run the project. Type: {project_type}"

    # Safety check: reject dangerous commands
    if not _is_safe_command(run_cmd):
        print(f"[Code] ⛔ Rejected unsafe command: {run_cmd}")
        # Fallback to detected run command
        detected = _detect_project_type(path)
        run_cmd = detected.get("run_cmd")
        if not run_cmd:
            return f"README contained unsafe commands and no safe run command could be determined. Type: {project_type}"

    print(f"[Code] ▶️ Running: {run_cmd}")

    # Step 5: Execute project
    try:
        result = subprocess.run(
            run_cmd, shell=True,
            capture_output=True, text=True,
            timeout=timeout, cwd=str(path)
        )
        output = result.stdout.strip()
        error = result.stderr.strip()
        combined = output + "\n" + error

        print(f"[Code] ✅ Project executed (exit code: {result.returncode})")

        # Step 6: Detect web server
        port = _detect_web_server(combined)
        web_msg = ""
        if port:
            url = f"http://localhost:{port}"
            web_msg = f"\n\n🌐 Web server detected on {url}"

            # Step 7: Open browser if requested
            if open_browser:
                try:
                    from actions.browser_control import browser_control
                    browser_control(
                        parameters={"action": "go_to", "url": url},
                        player=player
                    )
                    web_msg += " — opened in browser"
                except Exception as e:
                    web_msg += f" — failed to open browser: {e}"

        # Build result
        parts = [f"Project '{path.name}' ({project_type}) executed."]
        if "skipping" not in install_result.lower() and "failed" not in install_result.lower():
            parts.append(f"Install: {install_result[:150]}")
        parts.append(f"Command: {run_cmd}")

        if output:
            parts.append(f"Output:\n{output[:500]}")
        if error and result.returncode != 0:
            parts.append(f"Error:\n{error[:500]}")

        parts.append(web_msg)

        return "\n".join(parts)

    except subprocess.TimeoutExpired:
        # For long-running servers, check if it started successfully
        return (
            f"Project '{path.name}' started but is still running (timeout: {timeout}s). "
            f"This is normal for web servers. Command: {run_cmd}"
        )
    except FileNotFoundError:
        return f"Command not found: {run_cmd.split()[0]}. Is it installed?"
    except Exception as e:
        return f"Project execution failed: {e}"


def code_helper(
    parameters: dict,
    response=None,
    player=None,
    session_memory=None,
    speak=None
) -> str:
    """
    Called from main.py.

    parameters:
        action      : write | edit | explain | run | run_project | build | screen_debug | optimize | auto
        description : What the code should do / what change to make / what problem to analyze
        language    : Programming language (default: python)
        output_path : Where to save — user specifies full path or filename
        file_path   : Path to existing file (edit / explain / run / build / optimize)
        project_path: Path to project folder (run_project)
        code        : Raw code string (explain/optimize without a file)
        args        : CLI argument list for run/build
        timeout     : Execution timeout in seconds (default: 30)
        open_browser: Open browser if web server detected (default: true)
    """
    p           = parameters or {}
    action      = p.get("action", "auto").lower().strip()
    description = p.get("description", "").strip()
    language    = p.get("language", "python").strip()
    output_path = p.get("output_path", "").strip()
    file_path   = p.get("file_path", "").strip()
    project_path = p.get("project_path", "").strip()
    code        = p.get("code", "").strip()
    args        = p.get("args", [])
    timeout     = int(p.get("timeout", 30))
    open_browser = p.get("open_browser", True)

    if action == "auto":
        # If project_path provided, default to run_project
        if project_path:
            action = "run_project"
        else:
            action = _detect_intent(description, file_path, code)
            print(f"[Code] 🤖 Auto-detected: {action}")

    if action == "write":
        return _write_action(description, language, output_path, player)

    elif action == "edit":
        return _edit_action(
            file_path,
            description or p.get("instruction", ""),
            player
        )

    elif action == "explain":
        return _explain_action(file_path, code, player)

    elif action == "run":
        return _run_action(file_path, args, timeout, player)

    elif action == "run_project":
        if not project_path and file_path:
            # If only file_path given, use its parent directory
            project_path = str(Path(file_path).parent)
        return _run_project_action(project_path, timeout, open_browser, player)

    elif action == "build":
        return _build(description, language, output_path, args, timeout, speak, player)

    elif action == "optimize":
        return _optimize_action(file_path, code, language, output_path, player)

    elif action == "screen_debug":
        return _screen_debug_action(description, file_path, player, speak)

    else:
        return f"Unknown action: '{action}'. Use write, edit, explain, run, run_project, build, optimize, or screen_debug."