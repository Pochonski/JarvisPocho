import subprocess
import os
from pathlib import Path

PROJECTS_DIR = Path.home() / "Projects"


def _launch_terminal(project_path: Path, message: str) -> None:
    env = os.environ.copy()
    subprocess.Popen(
        [
            "uwsm-app", "--", "xdg-terminal-exec",
            f"--dir={project_path}",
            "opencode", str(project_path), "--prompt", message,
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def run_with_opencode(
    parameters: dict,
    player=None,
    session_memory=None,
) -> str:
    project = str(parameters.get("project", "")).strip()
    message = str(parameters.get("message", "")).strip()
    show_terminal = str(parameters.get("show_terminal", "false")).lower() in (
        "true", "1", "yes"
    )

    if not project:
        return "No project specified. Ask the user which project to run."

    if not message:
        return "No message provided for opencode."

    project_path = PROJECTS_DIR / project
    if not project_path.exists():
        for child in PROJECTS_DIR.iterdir():
            if child.is_dir() and child.name.lower() == project.lower():
                project_path = child
                project = child.name
                break
        else:
            return (
                f"Project '{project}' not found in {PROJECTS_DIR}. "
                f"Ask the user if the project name is correct."
            )

    if show_terminal:
        _launch_terminal(project_path, message)
        return f"OpenCode launched in '{project}' with your message."

    cmd = ["opencode", "run", message, "--dir", str(project_path)]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            error = (
                result.stderr.strip()[:500]
                or result.stdout.strip()[:500]
            )
            return f"OpenCode finished with code {result.returncode}: {error}"

        output = result.stdout.strip()
        return (
            output
            if output
            else f"OpenCode completed successfully in '{project}' but produced no output."
        )

    except subprocess.TimeoutExpired:
        return f"OpenCode timed out after 300s in '{project}'."
    except FileNotFoundError:
        return "OpenCode is not installed. Run: npm install -g opencode"
    except Exception as e:
        return f"Error running opencode: {e}"
