"""ZABACODE v1.0.0 — Native Kivy entry point."""

import os
import sys
import traceback
from pathlib import Path


def _write_crash_log() -> None:
    """Persist startup tracebacks where an Android user can retrieve them."""
    app_dir = Path(os.environ.get("ANDROID_PRIVATE", Path(__file__).parent))
    try:
        app_dir.mkdir(parents=True, exist_ok=True)
        (app_dir / "zabacode_crash.log").write_text(traceback.format_exc(), encoding="utf-8")
    except Exception:
        pass


if __name__ == "__main__":
    try:
        from zabacode.ui.app import ZabacodeApp
        ZabacodeApp().run()
    except Exception:
        _write_crash_log()
        raise
