"""
ZABACODE Core — Path Resolution & Directory Management
Handles APP_DIR detection for Android, Kivy, and Desktop environments.
"""

import os
from pathlib import Path


def resolve_app_dir() -> Path:
    """
    Resolve the application directory based on runtime environment.
    
    Priority:
    1. ANDROID_PRIVATE env var (Python-for-Android webview bootstrap)
    2. Kivy android storage via pyjnius
    3. Fallback: directory of this script
    """
    # 1. Android private storage (p4a sdl2 bootstrap)
    if "ANDROID_PRIVATE" in os.environ:
        return Path(os.environ["ANDROID_PRIVATE"])
    
    # 2. Kivy Android activity files dir
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity
        return Path(activity.getFilesDir().getAbsolutePath())
    except Exception:
        pass
    
    # 3. Desktop fallback
    return Path(__file__).parent.parent.resolve()


APP_DIR = resolve_app_dir()

# Critical directories
KEYS_FILE = APP_DIR / ".zabacode_keys_encrypted.json"
USER_PACKAGES_DIR = APP_DIR / "user_packages"
FILES_DIR = APP_DIR / "files"
CACHE_DIR = APP_DIR / "cache"
TOKEN_FILE = APP_DIR / ".zabacode_auth_token"
LOG_DIR = APP_DIR / "logs"

# Ensure all directories exist
for directory in [USER_PACKAGES_DIR, FILES_DIR, CACHE_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
