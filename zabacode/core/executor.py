"""
ZABACODE Core — Isolated & Interactive Subprocess Code Execution Engine
Runs user Python code in isolated or interactive subprocesses.
"""

import base64
import os
import queue
import signal
import subprocess
import sys
import threading
from pathlib import Path

from zabacode.core.paths import FILES_DIR, USER_PACKAGES_DIR, CACHE_DIR

# Limits
MAX_CODE_BYTES = 512 * 1024   # 512 KB
MAX_OUTPUT_CHARS = 256 * 1024  # 256 KB
DEFAULT_TIMEOUT = 30           # seconds


def _truncate(text: str) -> str:
    """Truncate output to prevent memory overflow."""
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return text[:MAX_OUTPUT_CHARS] + "\n[Output truncated]"


SAFE_INPUT_PATCH = """import builtins
_orig_input = builtins.input
def _safe_input(prompt=""):
    try:
        return _orig_input(prompt)
    except EOFError:
        return ""
builtins.input = _safe_input

"""

def normalize_code(code: str) -> str:
    """
    Normalize Python code to prevent EOF/syntax errors.
    - Convert Windows line endings (\r\n) to Unix (\n)
    - Remove BOM if present
    - Trim trailing whitespace per line
    - Handle from __future__ import statements properly at the absolute top of the file
    """
    code = code.replace('\r\n', '\n').replace('\r', '\n')
    if code.startswith('\ufeff'):
        code = code[1:]
    lines = code.split('\n')
    normalized_lines = [line.rstrip() for line in lines]

    # Extract __future__ imports to keep them at the absolute top of the generated file
    future_lines = []
    other_lines = []

    for line in normalized_lines:
        stripped = line.strip()
        if stripped.startswith('from __future__ import'):
            future_lines.append(line)
        else:
            other_lines.append(line)

    if future_lines:
        return '\n'.join(future_lines) + '\n\n' + SAFE_INPUT_PATCH + '\n'.join(other_lines)
    return SAFE_INPUT_PATCH + '\n'.join(normalized_lines)


def execute_code_isolated(code: str, stdin_data: str = "", timeout: int = DEFAULT_TIMEOUT) -> dict:
    """
    Run user code in a separate subprocess.
    This isolates process lifetime, not filesystem/network privileges.
    Treat code as trusted unless a platform-level sandbox is added.
    
    Returns dict with: ok, stdout, stderr, timeout, images
    """
    if not isinstance(code, str) or len(code.encode("utf-8")) > MAX_CODE_BYTES:
        return {
            "ok": False,
            "stdout": "",
            "stderr": "Source code terlalu besar.",
            "timeout": False,
            "images": []
        }

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    temp_script = FILES_DIR / "_active_run.py"
    
    try:
        code = normalize_code(code)
        temp_script.write_text(code, encoding="utf-8")
        
        env = os.environ.copy()
        python_path = f"{USER_PACKAGES_DIR}:{FILES_DIR}:{env.get('PYTHONPATH', '')}".strip(":")
        env["PYTHONPATH"] = python_path
        env["PYTHONNOUSERSITE"] = "1"
        env["TMPDIR"] = str(CACHE_DIR)
        env["TEMP"] = str(CACHE_DIR)
        env["TMP"] = str(CACHE_DIR)
        
        existing_images = set(FILES_DIR.glob("*.png")) | set(FILES_DIR.glob("*.jpg"))
        
        proc = subprocess.Popen(
            [sys.executable, "_active_run.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace",
            cwd=str(FILES_DIR),
            env=env,
            start_new_session=os.name != "nt",
        )
        
        try:
            stdout_text, stderr_text = proc.communicate(input=stdin_data, timeout=timeout)
        except subprocess.TimeoutExpired:
            if os.name != "nt":
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except OSError:
                    proc.kill()
            else:
                proc.kill()
            stdout_text, stderr_text = proc.communicate()
            return {
                "ok": False,
                "stdout": _truncate(stdout_text or ""),
                "stderr": _truncate(
                    (stderr_text or "").replace("_active_run.py", "main.py")
                    + f"\n[Process timed out after {timeout}s]"
                ),
                "timeout": True,
                "images": [],
            }

        new_images = (set(FILES_DIR.glob("*.png")) | set(FILES_DIR.glob("*.jpg"))) - existing_images
        image_data = []
        for img_path in sorted(new_images):
            try:
                b64 = base64.b64encode(img_path.read_bytes()).decode("utf-8")
                mime = "image/png" if img_path.suffix.lower() == ".png" else "image/jpeg"
                image_data.append({
                    "name": img_path.name,
                    "data_uri": f"data:{mime};base64,{b64}"
                })
            except Exception:
                pass

        stderr_cleaned = stderr_text.replace('_active_run.py', 'main.py') if stderr_text else ""

        return {
            "ok": proc.returncode == 0,
            "stdout": _truncate(stdout_text or ""),
            "stderr": _truncate(stderr_cleaned),
            "timeout": False,
            "images": image_data
        }
    except Exception as e:
        return {
            "ok": False,
            "stdout": "",
            "stderr": str(e),
            "timeout": False,
            "images": []
        }


# ---------------------------------------------------------------------------
# Interactive Subprocess Execution Engine
# ---------------------------------------------------------------------------

class InteractiveSession:
    def __init__(self):
        self.proc = None
        self.output_queue = queue.Queue()
        self.threads = []
        self.active = False


_session = InteractiveSession()


def _read_stream_char(stream, q, stream_type):
    """Asynchronously read characters from subprocess output streams."""
    try:
        while True:
            char = stream.read(1)
            if not char:
                break
            q.put((stream_type, char))
    except Exception:
        pass


def start_interactive_session(code: str) -> dict:
    """Spawns an interactive unbuffered subprocess and starts listener threads."""
    global _session
    stop_interactive_session()

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    temp_script = FILES_DIR / "_active_run.py"

    try:
        # Do not include safe input patch so input() acts interactively
        code_normalized = code.replace('\r\n', '\n').replace('\r', '\n')
        if code_normalized.startswith('\ufeff'):
            code_normalized = code_normalized[1:]

        temp_script.write_text(code_normalized, encoding="utf-8")

        env = os.environ.copy()
        python_path = f"{USER_PACKAGES_DIR}:{FILES_DIR}:{env.get('PYTHONPATH', '')}".strip(":")
        env["PYTHONPATH"] = python_path
        env["PYTHONNOUSERSITE"] = "1"
        env["TMPDIR"] = str(CACHE_DIR)
        env["TEMP"] = str(CACHE_DIR)
        env["TMP"] = str(CACHE_DIR)
        env["PYTHONUNBUFFERED"] = "1"

        _session.proc = subprocess.Popen(
            [sys.executable, "-u", "_active_run.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace",
            cwd=str(FILES_DIR),
            env=env,
            start_new_session=os.name != "nt",
        )
        _session.active = True
        _session.output_queue = queue.Queue()

        t_out = threading.Thread(target=_read_stream_char, args=(_session.proc.stdout, _session.output_queue, "stdout"), daemon=True)
        t_err = threading.Thread(target=_read_stream_char, args=(_session.proc.stderr, _session.output_queue, "stderr"), daemon=True)
        t_out.start()
        t_err.start()
        _session.threads = [t_out, t_err]

        return {"ok": True, "message": "Interactive process started"}
    except Exception as e:
        return {"ok": False, "message": f"Failed to start interactive session: {e}"}


def send_interactive_input(text: str) -> dict:
    """Send interactive input to the running subprocess's stdin."""
    global _session
    if not _session.active or not _session.proc:
        return {"ok": False, "message": "No active interactive session found."}

    try:
        _session.proc.stdin.write(text)
        _session.proc.stdin.flush()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "message": f"Failed to send input: {e}"}


def get_interactive_output() -> dict:
    """Collect all pending outputs from the unbuffered subprocess streams."""
    global _session
    if not _session.active or not _session.proc:
        return {"ok": False, "done": True, "output": []}

    output_chars = []
    while not _session.output_queue.empty():
        try:
            item = _session.output_queue.get_nowait()
            output_chars.append(item)
        except queue.Empty:
            break

    done = _session.proc.poll() is not None
    if done:
        _session.active = False
        exit_code = _session.proc.returncode
        return {"ok": True, "done": True, "output": output_chars, "exit_code": exit_code}

    return {"ok": True, "done": False, "output": output_chars}


def stop_interactive_session() -> dict:
    """Forcefully kills the active interactive subprocess and releases resources."""
    global _session
    if not _session.proc:
        return {"ok": False, "message": "No running process found."}

    try:
        if _session.proc.poll() is None:
            if os.name != "nt":
                try:
                    os.killpg(_session.proc.pid, signal.SIGKILL)
                except OSError:
                    _session.proc.kill()
            else:
                _session.proc.kill()
        _session.active = False
        _session.proc = None
        return {"ok": True, "message": "Process successfully stopped."}
    except Exception as e:
        return {"ok": False, "message": f"Failed to stop process: {e}"}
