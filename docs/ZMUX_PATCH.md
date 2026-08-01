# Patch untuk ZMUX (ZABAWHEELS) agar tidak tabrakan dengan ZABACODE

## Masalah
ZABACODE dan ZMUX keduanya `p4a.port = 5000`. Loopback shared, jadi second app load UI first app.

## Fix

### 1. app/buildozer.spec
```ini
# Before:
p4a.port = 5000

# After — distinct port:
p4a.port = 6000
android.manifest.launch_mode = singleTop
p4a.hook = tools/p4a_hook_zmux.py
```

### 2. app/zmux/server.py
```python
# Before:
P4A_HTTP_PORT = 5000

# After:
P4A_HTTP_PORT = 6000
```

### 3. tools/p4a_hook_zmux.py (buat file baru, mirip ZABACODE)
```python
from pathlib import Path
def _patch_manifest(p, package="com.zaba.zmux"):
    if not p.exists(): return False
    t = p.read_text(encoding="utf-8")
    orig = t
    if 'android:taskAffinity' in t:
        import re
        t = re.sub(r'android:taskAffinity="[^"]*"', f'android:taskAffinity="{package}"', t)
    else:
        marker = 'android:name="org.kivy.android.PythonActivity"'
        if marker in t:
            t = t.replace(marker, f'{marker}\n android:taskAffinity="{package}"\n android:documentLaunchMode="intoExisting"')
    if 'android:launchMode="singleTask"' in t:
        t = t.replace('android:launchMode="singleTask"', 'android:launchMode="singleTop"')
    if t != orig:
        p.write_text(t, encoding="utf-8")
        return True
    return False

def before_apk_build(toolchain):
    dist_dir = getattr(getattr(toolchain, "_dist", None), "dist_dir", None)
    if not dist_dir: return
    from pathlib import Path
    p = Path(dist_dir) / "src" / "main" / "AndroidManifest.xml"
    _patch_manifest(p)

def after_apk_build(toolchain):
    return before_apk_build(toolchain)
```

### 4. Build ulang
```bash
buildozer android debug
```

### 5. Tes
- Install Zabacode (5000) dan Zmux (6000) fresh
- Buka Zmux → cek log `Starting ZMUX ... 6000`
- Home → Buka Zabacode → cek log `Starting ZABACODE ... 5000`
- Seharusnya tidak ketuker lagi

Jika masih ketuker di launcher tertentu (Android Go), force-stop salah satu lalu buka lagi — kalau normal setelah force-stop, berarti taskAffinity fix bekerja.
