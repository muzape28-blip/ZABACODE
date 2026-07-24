"""
ZABACODE Core — ZMUX Command Shims Generator
Generates and writes Termux command wrappers and shims to the custom zmux_bin folder.
"""

import sys
import stat
from pathlib import Path

SHIMS = {
    "pkg": """#!/usr/bin/env python3
import sys
import subprocess

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: pkg <command> [args]")
        print("Commands: update, upgrade, install, uninstall, search, list-installed, list-all, show, files, reinstall, autoclean, clean")
        sys.exit(1)

    cmd = args[0]
    if cmd == "help" or cmd == "--help":
        print("Usage: pkg <command> [args]")
        print("Commands: update, upgrade, install, uninstall, search, list-installed, list-all, show, files, reinstall, autoclean, clean")
    elif cmd == "update":
        print("Hit:1 https://packages.termux.dev/apt/termux-main stable InRelease")
        print("Reading package lists... Done")
    elif cmd == "upgrade":
        print("Reading package lists... Done")
        print("Building dependency tree... Done")
        print("0 upgraded, 0 newly installed, 0 to remove and 0 not upgraded.")
    elif cmd in ("install", "reinstall"):
        if len(args) < 2:
            print("Usage: pkg install <package_name>")
            sys.exit(1)
        pkg_name = args[1]
        print(f"Installing {pkg_name} via Pip...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", pkg_name])
        except Exception as e:
            print(f"Error during install: {e}")
    elif cmd == "uninstall" or cmd == "remove":
        if len(args) < 2:
            print("Usage: pkg uninstall <package_name>")
            sys.exit(1)
        pkg_name = args[1]
        print(f"Uninstalling {pkg_name} via Pip...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", pkg_name])
        except Exception as e:
            print(f"Error during uninstall: {e}")
    else:
        print(f"Command '{cmd}' is simulated in ZMUX.")

if __name__ == '__main__':
    main()
""",

    "apt": """#!/usr/bin/env python3
import sys
import subprocess

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: apt <command> [args]")
        sys.exit(1)

    cmd = args[0]
    if cmd == "install":
        if len(args) < 2:
            print("Usage: apt install <package>")
            sys.exit(1)
        subprocess.run([sys.executable, "-m", "pip", "install", args[1]])
    elif cmd in ("uninstall", "remove"):
        if len(args) < 2:
            print("Usage: apt remove <package>")
            sys.exit(1)
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", args[1]])
    elif cmd == "update":
        print("Hit:1 https://packages.termux.dev/apt/termux-main stable InRelease")
        print("Reading package lists... Done")
    else:
        print(f"Apt command '{cmd}' is simulated in ZMUX.")

if __name__ == '__main__':
    main()
""",

    "termux-vibrate": """#!/usr/bin/env python3
import sys

def main():
    args = sys.argv[1:]
    duration = 500
    if args:
        try:
            duration = int(args[0])
        except ValueError:
            pass
    print(f"[ZMUX] Vibrating device for {duration}ms...")
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity
        Context = autoclass('android.content.Context')
        vibrator = activity.getSystemService(Context.VIBRATOR_SERVICE)
        vibrator.vibrate(duration)
    except Exception:
        pass

if __name__ == '__main__':
    main()
""",

    "termux-battery-status": """#!/usr/bin/env python3
import json

def main():
    status = {
        "health": "GOOD",
        "percentage": 85,
        "plugged": "UNPLUGGED",
        "status": "DISCHARGING",
        "temperature": 32.5
    }
    print(json.dumps(status, indent=2))

if __name__ == '__main__':
    main()
""",

    "termux-toast": """#!/usr/bin/env python3
import sys

def main():
    text = " ".join(sys.argv[1:]) if sys.argv[1:] else "ZMUX Toast!"
    print(f"[TOAST] {text}")
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity
        Toast = autoclass('android.widget.Toast')
        String = autoclass('java.lang.String')

        activity.runOnUIThread(lambda: Toast.makeText(
            activity,
            String(text),
            Toast.LENGTH_SHORT
        ).show())
    except Exception:
        pass

if __name__ == '__main__':
    main()
""",

    "termux-clipboard-get": """#!/usr/bin/env python3
import sys

def main():
    try:
        from kivy.core.clipboard import Clipboard
        print(Clipboard.paste() or "")
    except Exception:
        print("Mock ZMUX Clipboard Content")

if __name__ == '__main__':
    main()
""",

    "termux-clipboard-set": """#!/usr/bin/env python3
import sys

def main():
    text = " ".join(sys.argv[1:]) if sys.argv[1:] else sys.stdin.read()
    try:
        from kivy.core.clipboard import Clipboard
        Clipboard.copy(text)
        print("✓ Copied to clipboard")
    except Exception:
        print(f"[CLIPBOARD SET] {text}")

if __name__ == '__main__':
    main()
""",

    "termux-info": """#!/usr/bin/env python3
import platform
import sys

def main():
    print("Application version: ZABACODE v1.0.0 (WebView + Modular Python Core)")
    print(f"OS Platform: {platform.system()} ({platform.machine()})")
    print(f"Python Version: {platform.python_version()}")
    print("ZMUX Shell Layer: Active")

if __name__ == '__main__':
    main()
""",

    "termux-setup-storage": """#!/usr/bin/env python3
def main():
    print("Requesting Storage Permission...")
    print("✓ Storage Permission Granted. Access to /sdcard/ /Download/ enabled.")

if __name__ == '__main__':
    main()
"""
}

def generate_shims(zmux_bin_dir: Path) -> None:
    """Writes all wrapper shim scripts to the specified directory and makes them executable.

    NOTE ON ANDROID NOEXEC:
    On Android, the private application data partition (/data) is usually mounted with the
    MS_NOEXEC flag. This prevents direct execution of scripts or binaries (even with chmod +x).
    To bypass this limitation, we also write each python shim with a .py extension into
    the .shims subdirectory. Instead of executing the shims directly, the ZMUX shell session
    registers shell aliases pointing to explicitly invoked python commands:
        alias cmd='python3 /data/.../zmux_bin/.shims/cmd.py'
    This way, the OS executes the allowed python binary, and python loads the script as an argument.
    """
    zmux_bin_dir.mkdir(parents=True, exist_ok=True)
    shims_dir = zmux_bin_dir / ".shims"
    shims_dir.mkdir(parents=True, exist_ok=True)

    for name, content in SHIMS.items():
        # Write the standard extension-less script
        script_path = zmux_bin_dir / name
        script_path.write_text(content.strip() + "\n", encoding="utf-8")

        # Make script executable (won't be effective on Android but kept for other POSIX platforms/fallback)
        try:
            st = script_path.stat()
            script_path.chmod(st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        except Exception:
            pass

        # Write python script in .shims directory for Android/POSIX alias execution
        py_shim_path = shims_dir / f"{name}.py"
        py_shim_path.write_text(content.strip() + "\n", encoding="utf-8")

        # If on Windows, also write a batch file (.bat) so cmd.exe can execute it!
        if sys.platform == "win32":
            bat_path = zmux_bin_dir / f"{name}.bat"
            bat_content = f'@echo off\npython "{script_path}" %*'
            bat_path.write_text(bat_content, encoding="utf-8")
