# ZABACODE

[![Build Status](https://github.com/muzape28-blip/ZABACODE/actions/workflows/build_apk.yml/badge.svg)](https://github.com/muzape28-blip/ZABACODE/actions)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

**Zabacode** adalah IDE Python mobile standalone untuk Android (ARMv7 32-bit & ARM64 64-bit) yang menggabungkan kesederhanaan **Pydroid** dengan detail & completeness **Acode** — plus AI assistant gratis. 100% open-source, anti-kapitalis (zero telemetry), bertujuan F-Droid.

```
┌──────────────────────────────────────────────────────────┐
│  ZABACODE v0.3.0                                         │
│  [ OK ] Subprocess sandbox Python engine ready           │
│  [ OK ] Multi-tab adaptive Monaco / Native editor loaded │
│  [ OK ] Dedicated Library Manager (zabapip) active       │
│  [ OK ] Multi-provider AI (Qwen 2.5, Gemini, Groq) ready │
│  > workspace ready_                                      │
└──────────────────────────────────────────────────────────┘
```

## Features & What's New in v0.3.0

🚀 **Overhauled Library Manager Overlay (`zabapip`)**
- Diubah dari daftar samping menjadi **Dedicated Layer/Overlay View** penuh dengan tampilan Card Grid, pencarian real-time, dan filter kategori (`🌟 Semua`, `🌐 Web & API`, `📊 Data & Sains`, `🤖 AI & Database`, `🎨 Media & Utils`).
- **Custom PyPI Installer**: Memungkinkan pengguna memasukkan dan menginstall *pustaka apa saja* dari PyPI secara langsung via `pip install --target`.
- Pustaka bawaan terintegrasi mencakup `requests`, `beautifulsoup4`, `httpx`, `fastapi`, `flask`, `tinydb`, `sqlalchemy`, `sympy`, `rich`, `colorama`, `pydantic`, dan puluhan lainnya.

📁 **Multi-Tab File System Manager**
- Pengguna dapat membuka dan berpindah antar-beberapa file Python sekaligus menggunakan tab bar interaktif di atas editor.

🖼️ **Inline Output Image / Graphic Plot Rendering**
- Eksekusi kode yang menghasilkan file gambar/grafik (seperti plot Matplotlib atau objek Pillow) secara otomatis dideteksi dan ditampilkan *inline* di terminal output.

🤖 **Updated Multi-Provider AI Assistant**
- OpenRouter (`qwen/qwen-2.5-coder-32b-instruct:free`), Google Gemini (`gemini-1.5-flash`), Groq (`llama-3.1-8b-instant`), dan Mistral (`codestral-latest`).
- **`⚡ ZABA AI: BENERIN ERROR INI!`**: Tombol auto-fix otomatis di terminal untuk analisis dan solusi perbaikan instan saat terjadi Traceback error.

📱 **Dual-Arch Android Support**
- `buildozer.spec` kini mendukung baik `armeabi-v7a` (32-bit) maupun `arm64-v8a` (64-bit) untuk kinerja optimal di HP Android modern maupun lawas.

## Quick Start

### Development

```bash
# Clone repo
git clone https://github.com/muzape28-blip/ZABACODE.git
cd ZABACODE

# Install dev dependencies
pip install -r requirements-dev.txt

# Run Flask backend (localhost:5000)
python main.py

# Open browser: http://localhost:5000
```

### Build APK via GitHub Actions

```bash
git push origin main
# Actions otomatis mengompilasi APK untuk ARMv7 dan ARM64!
```

## License

GPL v3 License. See LICENSE for details.
