[app]
title = Zabacode
package.name = zabacode
package.domain = com.zaba
source.dir = .
source.include_exts = py,png,jpg,html,js,css,json
version = 0.1.0

# CATATAN: baru requirement minimal buat Milestone 1 (hello world + AI chat
# lewat urllib bawaan). Tambahin library lain di sini (numpy, dst) pas
# butuh beneran — itu yang bikin rebuild lewat GitHub Actions perlu jalan
# lagi, bukan sesuatu yang user install sendiri di app yang udah jadi.
requirements = python3,flask,waitress

# Seluruh UI Zabacode adalah satu WebView yang nampilin localhost, di-serve
# oleh Flask yang jalan di thread Python background (lihat main.py).
p4a.bootstrap = webview

orientation = portrait
fullscreen = 0

# HP target Zaqi: ARMv7 32-bit, RAM kecil, Android 8+ (API 26+).
# Kalau nanti mau nambahin dukungan HP 64-bit juga, tinggal tambah
# arm64-v8a di baris ini.
android.archs = armeabi-v7a
android.api = 31
android.minapi = 26
android.ndk_api = 21
android.permissions = INTERNET

[buildozer]
log_level = 2
warn_on_root = 1

# ============================================================================
# JUJUR: file ini ditulis berdasar riset dokumentasi buildozer/p4a, BUKAN
# hasil compile beneran (sandbox Claude ga ada akses internet buat jalanin
# buildozer/Android SDK/NDK). Kemungkinan besar ada 1-2 baris yang perlu
# disesuaikan pas run pertama di GitHub Actions — itu normal buat proyek
# buildozer manapun. Cek log error-nya, biasanya jelas apa yang kurang.
# ============================================================================
