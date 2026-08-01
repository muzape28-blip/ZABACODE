[app]

title = Zabacode
package.name = zabacode
package.domain = com.zaba
source.dir = .
source.include_exts = py,png,jpg,html,js,css,json,ttf,otf
version = 1.2.1

# --- Icon (Fixed: Square 1024x1024 PNG, no white border, no JPEG letterbox) ---
# Previously 1376x768 JPEG with black letterbox causing white rounded square in launcher (issue #2)
icon.filename = %(source.dir)s/assets/logo.png

# --- Presplash (Fixed: Purple bars white screen is default p4a loading when no presplash set) ---
presplash.filename = %(source.dir)s/assets/presplash.png
presplash_color = #050806

# WebView shell over the v1.2.0 modular Python core (not Kivy)
# COEXISTENCE FIX (2026): Zabacode and Zmux both used p4a.port = 5000.
# Loopback 127.0.0.1 is shared across apps, so second app would bind 5001
# but WebViewLoader still pings 5000 and loads the first app's UI.
# Fix: keep distinct ports per app (Zabacode 5000, Zmux 6000) and bind strictly.
p4a.bootstrap = webview
p4a.port = 5000

# Core requirements
requirements = python3,flask,waitress,pip,setuptools,requests,tinydb,beautifulsoup4,python-dotenv,certifi,openssl

orientation = portrait
fullscreen = 0

# Android specific
android.archs = armeabi-v7a, arm64-v8a
android.accept_sdk_license = True
android.api = 34
android.minapi = 26
android.ndk_api = 26
android.permissions = INTERNET
android.allow_backup = False
android.orientation = portrait

# Android Manifest — taskAffinity / launchMode coexistence fix
# NOTE: buildozer has NO property "android.taskAffinity" — that key is ignored (verified in
# buildozer/targets/android.py). Use android.manifest.launch_mode + p4a hook to inject affinity.
# - singleTop reduces aggressive task reuse vs default singleTask, while still avoiding duplicates
# - p4a.hook = tools/p4a_hook.py injects android:taskAffinity="com.zaba.zabacode"
android.manifest.launch_mode = singleTop

# p4a manifest hook — patches AndroidManifest.xml to inject explicit taskAffinity
# See tools/p4a_hook.py for implementation (uses after_apk_build / before_apk_build)
p4a.hook = tools/p4a_hook.py

# Adaptive Icon (Fix launcher white square issue - screenshot 2)
# Android 8+ adaptive icons need background + foreground
android.adaptive_icon_background = #050806
android.adaptive_icon_foreground = %(source.dir)s/assets/logo.png

# Presplash color for Android (fixes white screen with purple bars - screenshot 3)
android.presplash_color = #050806
android.presplash = %(source.dir)s/assets/presplash.png

[buildozer]
log_level = 2
warn_on_root = 1
