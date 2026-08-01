"""
ZABACODE p4a hook — inject explicit taskAffinity + documentLaunchMode

Background:
- Both Zabacode and Zmux used p4a.port=5000 and org.kivy.android.PythonActivity
- Loopback 127.0.0.1 is shared, so second app's WebViewLoader (hardcoded 5000)
  would load first app's Flask UI => "buka zabacode muncul zmux"
- Additionally, Android singleTask + identical activity class name can cause
  launcher to bring wrong task to front on some OEM launchers (Android Go)

Fix:
- Python side: strict bind to 5000 (no range scan) + distinct ports per app
  (Zabacode 5000, Zmux 6000) — see web_app.py P4A_HTTP_PORT
- Manifest side: inject explicit android:taskAffinity and
  android:documentLaunchMode="intoExisting" + ensure launchMode=singleTop
  so system can differentiate tasks by ComponentName + data URI + affinity.

This hook edits src/main/AndroidManifest.xml after p4a generates it but before
gradle packages the APK. It is referenced in buildozer.spec as p4a.hook.

Buildozer has NO property "android.taskAffinity" — that key is ignored.
The official way is via hook (see https://github.com/kivy/python-for-android/pull/2691
discussion, gist.github.com/tito/4f75385054222182e4f0cf56c90dcdf8).

Usage in buildozer.spec:
  android.manifest.launch_mode = singleTop
  p4a.hook = tools/p4a_hook.py
"""

from pathlib import Path

# Try to import ToolchainCL for type hint, but don't fail if p4a not installed
try:
    from pythonforandroid.toolchain import ToolchainCL  # type: ignore
except Exception:
    ToolchainCL = object


def _patch_manifest(manifest_path: Path, package: str = "com.zaba.zabacode"):
    if not manifest_path.exists():
        print(f"[p4a_hook] Manifest not found at {manifest_path}, skipping")
        return False

    text = manifest_path.read_text(encoding="utf-8")
    original = text

    # Desired affinity — must contain a dot per Android validation, and be unique per app
    affinity = package
    # Ensure activity has explicit taskAffinity and documentLaunchMode
    # The webview bootstrap template has:
    #   <activity android:name="org.kivy.android.PythonActivity" ...>
    # We inject attributes before the closing ">"
    # Patch approach: replace first occurrence of PythonActivity tag with enhanced one

    # If taskAffinity already present, replace it; otherwise inject
    if 'android:taskAffinity' in text:
        print("[p4a_hook] taskAffinity already present, updating")
        # simple regex-free replace: if existing affinity, ensure it's our package
        # replace whatever value with our desired affinity
        import re
        text = re.sub(
            r'android:taskAffinity="[^"]*"',
            f'android:taskAffinity="{affinity}"',
            text,
        )
    else:
        # Inject into activity tag
        # Find <activity android:name="org.kivy.android.PythonActivity"
        marker = 'android:name="org.kivy.android.PythonActivity"'
        if marker in text:
            # inject after marker
            text = text.replace(
                marker,
                f'{marker}\n                  android:taskAffinity="{affinity}"\n                  android:documentLaunchMode="intoExisting"',
            )
            print(f"[p4a_hook] Injected taskAffinity={affinity} + documentLaunchMode=intoExisting")
        else:
            print("[p4a_hook] PythonActivity marker not found, trying broader patch")
            # fallback: inject into first <activity>
            text = text.replace(
                "<activity",
                f'<activity android:taskAffinity="{affinity}" android:documentLaunchMode="intoExisting"',
                1,
            )

    # Ensure application tag also has distinct affinity? Usually activity affinity is enough,
    # but we can also set application-level taskAffinity via extra manifest application arguments
    # if template supports it. Since webview template doesn't, we set only activity.

    # Ensure launchMode is singleTop (if template still has singleTask from default)
    # buildozer.spec android.manifest.launch_mode should already set it, but enforce here
    if 'android:launchMode="singleTask"' in text:
        text = text.replace('android:launchMode="singleTask"', 'android:launchMode="singleTop"')
        print("[p4a_hook] Changed launchMode singleTask -> singleTop for safer co-existence")

    if text != original:
        manifest_path.write_text(text, encoding="utf-8")
        print(f"[p4a_hook] Patched manifest at {manifest_path}")
        return True
    else:
        print("[p4a_hook] No changes made to manifest")
        return False


def before_apk_build(toolchain):
    """Hook called by p4a before APK build — patch dist's AndroidManifest."""
    dist_dir = getattr(getattr(toolchain, "_dist", None), "dist_dir", None)
    if not dist_dir:
        # try alternative attribute
        dist_dir = getattr(toolchain, "dist_dir", None)
    if not dist_dir:
        print("[p4a_hook] before_apk_build: dist_dir not found, trying default path")
        # fallback: search common buildozer path
        possible = Path(".buildozer/android/platform/build-arm64-v8a_armeabi-v7a/dists/zabacode/src/main/AndroidManifest.xml")
        if possible.exists():
            _patch_manifest(possible)
        return

    dist_path = Path(dist_dir)
    # Common locations
    candidates = [
        dist_path / "src" / "main" / "AndroidManifest.xml",
        dist_path / "src" / "main" / "AndroidManifest.xml",  # duplicate but ok
        dist_path / "templates" / "AndroidManifest.tmpl.xml",
    ]
    patched = False
    for cand in candidates:
        if cand.exists():
            if _patch_manifest(cand):
                patched = True
    if not patched:
        # also try build folder
        build_root = Path(".buildozer")
        for mf in build_root.rglob("AndroidManifest.xml"):
            if "zabacode" in str(mf).lower() or "zmux" not in str(mf).lower():
                if _patch_manifest(mf):
                    patched = True
                    break


def after_apk_build(toolchain):
    """Hook called after APK build — also patch for completeness and log."""
    # Re-use same logic
    return before_apk_build(toolchain)


# For local testing without p4a toolchain
if __name__ == "__main__":
    import sys
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".buildozer/android/platform/build-arm64-v8a_armeabi-v7a/dists/zabacode/src/main/AndroidManifest.xml")
    _patch_manifest(path)
