[app]

title = Zabacode
package.name = zabacode
package.domain = com.zaba
source.dir = .
source.include_exts = py,png,jpg,html,js,css,json,ttf,otf
version = 1.0.0

# (string) Icon of the application
icon.filename = %(source.dir)s/assets/logo.png

# WebView shell over the v1.0.0 modular Python core
p4a.bootstrap = webview
p4a.port = 5000

# Core requirements
requirements = python3,flask,waitress,pip,setuptools,requests,tinydb,beautifulsoup4,python-dotenv

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
