[app]

title = Zabacode
package.name = zabacode
package.domain = com.zaba
source.dir = .
source.include_exts = py,png,jpg,json,ttf,otf
version = 1.0.0

# Kivy native UI (sdl2 bootstrap, NOT webview!)
p4a.bootstrap = sdl2

# Core requirements
requirements = python3,kivy,pygments,pip,setuptools,requests,tinydb,beautifulsoup4,python-dotenv

orientation = portrait
fullscreen = 0

android.archs = armeabi-v7a, arm64-v8a
android.accept_sdk_license = True
android.api = 34
android.minapi = 26
android.ndk_api = 26
android.permissions = INTERNET
android.allow_backup = False

# Kivy orientation
android.orientation = portrait

# Presplash
# android.presplash_color = #050806

[buildozer]
log_level = 2
warn_on_root = 1
