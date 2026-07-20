# ZABACODE

[![Build Status](https://github.com/muzape28-blip/ZABACODE/actions/workflows/build_apk.yml/badge.svg)](https://github.com/muzape28-blip/ZABACODE/actions)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

**Zabacode** adalah IDE Python mobile standalone untuk Android (ARMv7 32-bit & ARM64 64-bit) yang menggabungkan kesederhanaan **Pydroid** dengan detail & completeness **Acode** — plus AI assistant gratis. 100% open-source, anti-kapitalis (zero telemetry), bertujuan F-Droid.

```
┌──────────────────────────────────────────────────────────┐
│  ZABACODE v0.3.3                                         │
│  [ OK ] Subprocess sandbox Python engine ready           │
│  [ OK ] __file__ Path Resolver active (_active_run.py)   │
│  [ OK ] PyPI Direct Extractor active (SIGSEGV bypass)    │
│  [ OK ] Multi-tab adaptive editor & In-App Docs ready    │
│  [ OK ] Multi-provider AI (Qwen 2.5, Gemini, Groq) ready │
│  > workspace ready_                                      │
└──────────────────────────────────────────────────────────┘
```

## Features & Critical Fixes in v0.3.3

🛠️ **Automatic Script File Execution (`__file__` Fixed)**
- Mengganti eksekusi `-c` mentah dengan file temporary `_active_run.py`.
- **`Path(__file__)` terdefinisi sempurna**, sehingga script seperti `mjurran.py` yang menggunakan `Path(__file__).parent` tidak akan pernah mengalami `NameError: name '__file__' is not defined`.

📦 **Direct PyPI Wheel Extractor (Bypass `pip error (-11)`)**
- Dilengkapi dengan *Automatic Pure Python Extractor* via PyPI JSON API. Jika eksekusi `pip` subprocess bawaan mengalami `SIGSEGV (-11)` akibat pembatasan kernel Android, Zabacode secara otomatis mengunduh `.whl` murni Python dan mengekstraknya via `zipfile` internal tanpa bergantung pada compiler C.

📖 **In-App Navigation & Theme Lock (No White Line Glitch)**
- Dokumentasi & Roadmap dibuka dalam **Modal Internal** tanpa mengalihkan browser WebView ke luar, mencegah hilangnya state / tema editor.
- **Aktifkan `pageshow` listener & matikan `lineHighlight` Monaco** untuk membasmi garis putih horisontal secara permanen.

🤖 **Multi-Provider AI Assistant & Auto-Fix**
- OpenRouter (`qwen/qwen-2.5-coder-32b-instruct:free`), Google Gemini (`gemini-1.5-flash`), Groq (`llama-3.1-8b-instant`), dan Mistral (`codestral-latest`).
- **`⚡ ZABA AI: BENERIN ERROR INI!`**: Tombol auto-fix otomatis di terminal saat Traceback terjadi.

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
