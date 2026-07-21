"""
ZABACODE Core — Isolated Subprocess Code Execution Engine
Runs user Python code in isolated subprocess with timeout, __file__ resolution, and image capture.
"""

import base64
import os
import signal
import subprocess
import sys
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


def normalize_code(code: str) -> str:
    """
    Normalize Python code to prevent EOF/syntax errors.
    - Convert Windows line endings (\\r\\n) to Unix (\\n)
    - Remove BOM if present
    - Trim trailing whitespace per line
    """
    code = code.replace('\r\n', '\n').replace('\r', '\n')
    if code.startswith('\ufeff'):
        code = code[1:]
    lines = code.split('\n')
    normalized_lines = [line.rstrip() for line in lines]
    return '\n'.join(normalized_lines)


def execute_code_isolated(code: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
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
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace",
            cwd=str(FILES_DIR),
            env=env,
            start_new_session=os.name != "nt",
        )
        
        try:
            stdout_text, stderr_text = proc.communicate(timeout=timeout)
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
