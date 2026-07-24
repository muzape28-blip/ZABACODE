"""
ZABACODE Core — ZMUX Interactive Terminal Engine
Spawns local shell sessions, manages non-blocking stdout/stderr reading, and injects custom shims.
"""

import os
import queue
import signal
import subprocess
import sys
import threading
from pathlib import Path

from zabacode.core.paths import APP_DIR, FILES_DIR

class ZmuxSession:
    def __init__(self):
        self.proc = None
        self.output_queue = queue.Queue()
        self.threads = []
        self.active = False

_zmux = ZmuxSession()

def _read_zmux_stream(stream, q, stream_type):
    """Asynchronously read from the shell subprocess output streams."""
    try:
        # Read character by character for high real-time responsiveness
        while True:
            char = stream.read(1)
            if not char:
                break
            q.put((stream_type, char))
    except Exception:
        pass

def start_zmux_session() -> dict:
    """Spawns an interactive shell session with custom $PATH to run shims."""
    global _zmux
    stop_zmux_session()

    # Determine shell path
    if os.name == "nt":
        shell_cmd = ["cmd.exe"]
    else:
        # Check if bash exists, fallback to sh
        if Path("/bin/bash").exists():
            shell_cmd = ["/bin/bash"]
        elif Path("/system/bin/sh").exists():
            shell_cmd = ["/system/bin/sh"]
        else:
            shell_cmd = ["/bin/sh"]

    # Setup custom zmux_bin path
    zmux_bin_dir = APP_DIR / "zmux_bin"
    zmux_bin_dir.mkdir(parents=True, exist_ok=True)

    # Generate shims
    from zabacode.core.zmux_shims import generate_shims
    generate_shims(zmux_bin_dir)

    try:
        env = os.environ.copy()

        # Inject zmux_bin to front of PATH so our shims (pkg, apt, termux-*) take precedence
        path_sep = ";" if os.name == "nt" else ":"
        env["PATH"] = f"{zmux_bin_dir}{path_sep}{env.get('PATH', '')}"

        # Also let Python interpreter know about our core packages
        env["PYTHONPATH"] = f"{APP_DIR}:{env.get('PYTHONPATH', '')}".strip(path_sep)
        env["PYTHONUNBUFFERED"] = "1"

        _zmux.proc = subprocess.Popen(
            shell_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace",
            cwd=str(FILES_DIR),
            env=env,
            start_new_session=os.name != "nt",
        )
        _zmux.active = True
        _zmux.output_queue = queue.Queue()

        t_out = threading.Thread(target=_read_zmux_stream, args=(_zmux.proc.stdout, _zmux.output_queue, "stdout"), daemon=True)
        t_err = threading.Thread(target=_read_zmux_stream, args=(_zmux.proc.stderr, _zmux.output_queue, "stderr"), daemon=True)
        t_out.start()
        t_err.start()
        _zmux.threads = [t_out, t_err]

        # Put a cool startup banner / welcome text in the queue
        banner = (
            "\r\n"
            "┌────────────────────────────────────────────────────────┐\r\n"
            "│ ⚡ ZMUX TERMINAL — Fully Interactive Local Shell ⚡      │\r\n"
            "│ [ OK ] Connected to Local Subprocess                   │\r\n"
            "│ [ OK ] Shim Layer Loaded ($PATH Pre-empted)            │\r\n"
            "│                                                        │\r\n"
            "│ Type 'pkg' or 'termux-info' for commands list!         │\r\n"
            "└────────────────────────────────────────────────────────┘\r\n"
            "\r\n"
        )
        for char in banner:
            _zmux.output_queue.put(("stdout", char))

        if os.name != "nt":
            _zmux.proc.stdin.write("\n")
            _zmux.proc.stdin.flush()

        return {"ok": True, "message": "ZMUX session started"}
    except Exception as e:
        return {"ok": False, "message": f"Failed to start ZMUX session: {e}"}

def send_zmux_input(text: str) -> dict:
    """Send user input to the running ZMUX shell."""
    global _zmux
    if not _zmux.active or not _zmux.proc:
        return {"ok": False, "message": "No active ZMUX session."}
    try:
        _zmux.proc.stdin.write(text)
        _zmux.proc.stdin.flush()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "message": f"Failed to send input: {e}"}

def get_zmux_output() -> dict:
    """Collect all pending outputs from the ZMUX shell session."""
    global _zmux
    if not _zmux.active or not _zmux.proc:
        return {"ok": False, "done": True, "output": []}

    output_chars = []
    while not _zmux.output_queue.empty():
        try:
            item = _zmux.output_queue.get_nowait()
            output_chars.append(item)
        except queue.Empty:
            break

    done = _zmux.proc.poll() is not None
    if done:
        _zmux.active = False
        exit_code = _zmux.proc.returncode
        return {"ok": True, "done": True, "output": output_chars, "exit_code": exit_code}

    return {"ok": True, "done": False, "output": output_chars}

def stop_zmux_session() -> dict:
    """Forcefully kills the active ZMUX subprocess."""
    global _zmux
    if not _zmux.proc:
        return {"ok": False, "message": "No running ZMUX session."}
    try:
        if _zmux.proc.poll() is None:
            if os.name != "nt":
                try:
                    os.killpg(_zmux.proc.pid, signal.SIGKILL)
                except OSError:
                    _zmux.proc.kill()
            else:
                _zmux.proc.kill()
        _zmux.active = False
        _zmux.proc = None
        return {"ok": True, "message": "ZMUX session stopped."}
    except Exception as e:
        return {"ok": False, "message": f"Failed to stop ZMUX: {e}"}
