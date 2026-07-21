[app]
title = Zabacode
package.name = zabacode
package.domain = com.zaba
source.dir = .
source.include_exts = py,png,jpg,html,js,css,json
version = 0.3.4

requirements = python3,pip,setuptools,flask,waitress,requests,tinydb,beautifulsoup4,python-dotenv

p4a.bootstrap = webview
p4a.port = 5000

orientation = portrait
fullscreen = 0

android.archs = armeabi-v7a, arm64-v8a
android.accept_sdk_license = True
android.api = 34
android.minapi = 26
android.ndk_api = 26
android.permissions = INTERNET

[buildozer]
log_level = 2
warn_on_root = 1
