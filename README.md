# ZABACODE

[![Build Status](https://github.com/muzape28-blip/ZABACODE/actions/workflows/build_apk.yml/badge.svg)](https://github.com/muzape28-blip/ZABACODE/actions)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

**Zabacode** adalah IDE Python mobile standalone untuk Android (ARMv7 32-bit & ARM64 64-bit) yang menggabungkan kesederhanaan **Pydroid** dengan detail & completeness **Acode** — plus AI assistant gratis. 100% open-source, anti-kapitalis (zero telemetry), bertujuan F-Droid.

```
┌──────────────────────────────────────────────────────────┐
│  ZABACODE v0.3.4                                         │
│  [ OK ] Subprocess sandbox Python engine ready           │
│  [ OK ] __file__ Path Resolver active (_active_run.py)   │
│  [ OK ] PyPI Direct Extractor active (SIGSEGV bypass)    │
│  [ OK ] Dual Engine Support: Monaco & Native Engine      │
│  [ OK ] Total Cleared Active Line Highlight              │
│  [ OK ] Multi-provider AI (Qwen 2.5, Gemini, Groq) ready │
│  > workspace ready_                                      │
└──────────────────────────────────────────────────────────┘
```

## What's New in v0.3.4

🚫 **100% Cleared Active Line White Highlight (Garis Putih Total Hilang)**
- Menghapus border, outline, dan highlight aktif bawaan Android WebKit & Monaco Editor yang menutupi baris kode pertama.
- Menambahkan **`⚙️ Engine Switcher Button`** di sidebar menu untuk berpindah antara **Monaco Engine** dan **Native Light Engine** kapan saja secara fleksibel.

🛠️ **Automatic Script File Execution (`__file__` Fixed)**
- Mengganti eksekusi `-c` mentah dengan file temporary `_active_run.py`.
- **`Path(__file__)` terdefinisi sempurna**, sehingga script seperti `mjurran.py` yang menggunakan `Path(__file__).parent` tidak akan pernah mengalami `NameError: name '__file__' is not defined`.

📦 **Direct PyPI Wheel Extractor (Bypass `pip error (-11)`)**
- Dilengkapi dengan *Automatic Pure Python Extractor* via PyPI JSON API. Jika eksekusi `pip` subprocess bawaan mengalami `SIGSEGV (-11)` akibat pembatasan kernel Android, Zabacode secara otomatis mengunduh `.whl` murni Python dan mengekstraknya via `zipfile` internal tanpa bergantung pada compiler C.

📖 **In-App Modal Navigation**
- Dokumentasi & Roadmap dibuka dalam Modal Internal tanpa mengalihkan browser WebView ke luar, menjaga tema & state editor tetap utuh.

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
