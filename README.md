<p align="center">
  <img src="assets/logo.png" alt="ZABACODE Logo" width="220" height="220">
</p>

<h1 align="center">⚡ ZABACODE ⚡</h1>

<p align="center">
  <b>Standalone Anti-Capitalist Mobile Python IDE & AI Code Assistant for Android</b>
</p>

<p align="center">
  <i>Combining the raw execution power of <b>Pydroid 3</b> with the detail, multi-tab elegance & UI control of <b>Acode</b> — 100% Free, Open Source, & Zero Telemetry.</i>
</p>

<p align="center">
  <a href="README_ID.md"><b>🇮🇩 Baca Dokumentasi Bahasa Indonesia</b></a>
</p>

<p align="center">
  <a href="https://github.com/muzape28-blip/ZABACODE/actions/workflows/build_apk.yml"><img src="https://github.com/muzape28-blip/ZABACODE/actions/workflows/build_apk.yml/badge.svg" alt="Build Status"></a>
  <a href="https://github.com/muzape28-blip/ZABACODE/releases"><img src="https://img.shields.io/badge/Release-v0.3.5-39FF14.svg?style=flat&logo=android" alt="Version"></a>
  <a href="https://www.gnu.org/licenses/gpl-3.0"><img src="https://img.shields.io/badge/License-GPLv3-blue.svg" alt="GPLv3 License"></a>
  <img src="https://img.shields.io/badge/Architecture-ARMv7%20%7C%20ARM64-FFB000.svg" alt="Architecture">
  <img src="https://img.shields.io/badge/Telemetry-ZERO-brightgreen.svg" alt="Zero Telemetry">
  <img src="https://img.shields.io/badge/Privacy-100%25%20Offline%20First-success.svg" alt="Offline First">
</p>

---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ZABACODE — Mobile Engine Active                                            │
│  [ OK ] Subprocess Sandbox Engine Ready                                     │
│  [ OK ] Local Session Auth Token Security Active (X-Zabacode-Token)         │
│  [ OK ] Android Keystore Encrypted Key Storage Active                       │
│  [ OK ] Path Resolver Active (_active_run.py -> Path(__file__) OK)          │
│  [ OK ] Direct PyPI Wheel Extractor Active (SSL & SIGSEGV -11 Bypass)       │
│  [ OK ] Dual Engine Core: Monaco (Deterministic LineHeight) + Native Engine │
│  [ OK ] Bilingual Support Engine Active (Indonesian & English i18n)         │
│  > WORKSPACE READY. HAPPY CODING!_                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏛️ Lore & Philosophy

The name **ZABACODE** is inspired by **Zabaniyah** — the legendary guardian entities known for their uncompromising strength and vigilance. 

In a mobile software ecosystem overcrowded with invasive ads, aggressive paywalls, personal data mining (*telemetry*), and expensive subscriptions, **ZABACODE stands as an anti-capitalist statement**:
* **100% Free & Open-Source (GPLv3)**
* **Zero Banner Ads or Annoying Pop-ups**
* **Zero Telemetry / Zero Tracking**
* **100% Isolated Local Code Execution (Offline First)**

---

## ✨ Key Features & Improvements

### 🧠 1. Subprocess Isolation & Auto `__file__` Resolution
* **Full Process Isolation:** Every Python script is executed inside an isolated subprocess with a 30-second execution timeout.
* **Automatic `__file__` Resolution:** Scripts are executed via a temporary script file `_active_run.py`, guaranteeing that calls to `Path(__file__)` or `__file__` **succeed 100%** without throwing `NameError: name '__file__' is not defined`.

### 📦 2. Library Manager (`zabapip`) & Direct PyPI Extractor
* **SIGSEGV (-11) & SSL Bypass:** If standard `pip` crashes on Android, Zabacode seamlessly falls back to querying the PyPI JSON API with a bypass SSL context, fetching pure Python Wheel archives (`.whl`), and unzipping them directly into `user_packages`.
* **Custom PyPI Installer:** Install any package from PyPI on the fly.

### ⚙️ 3. Monaco Cursor Alignment Fix & Bilingual i18n Engine
* **Deterministic LineHeight:** Fixes visual caret cursor positioning in Monaco Editor on Android WebViews by configuring exact 22px line height metrics.
* **Instant Language Toggle:** Easily switch the entire IDE UI between **Indonesian** and **English** with 1 click in the sidebar menu.
* **Clean Header:** Topbar displays clean `ZABACODE` title.

### 🧩 4. Functional Plugin & Theme Marketplace
* **Addon Marketplace:** Features 1-click active plugins:
  * ⚡ **Auto-Code Formatter (PEP-8)**
  * 📜 **Pro Python Snippets Pack**
  * 🔍 **Static Syntax Linter Guard**
  * ⌨️ **Extended Mobile Symbol Bar** (Quick symbol toolbar above keyboard)
  * 🎨 **Themes Pack:** Cyberpunk Neon, Nord Arctic, Monokai Pro, Dracula, Solarized Dark, Retro Green.

---

## 🏗️ Architecture & Data Flow

```
 ┌─────────────────────────────────────────────────────────┐
│              Android Webview Front-End UI               │
│    (Adaptive Monaco Editor / Native Engine + i18n UI)   │
└────────────────────────────┬────────────────────────────┘
                             │ HTTP REST API (127.0.0.1:5000 + Token)
┌────────────────────────────▼────────────────────────────┐
│              Flask + Waitress Backend Server            │
│                     (main.py)                           │
└─────┬──────────────────────┬──────────────────────┬─────┘
      │                      │                      │
┌─────▼───────────────┐ ┌────▼───────────────┐ ┌────▼───────────────┐
│ Isolated Subprocess │ │ Direct PyPI Extractor│ │ Multi-Provider AI │
│ Code Execution Engine│ │  (urllib + zipfile)│ │ (OpenRouter/Gemini│
│ (_active_run.py)    │ │  (user_packages)   │ │  /Groq/Mistral)   │
└─────────────────────┘ └────────────────────┘ └───────────────────┘
```

---

## 📊 Comparison: ZABACODE vs Pydroid 3 vs Acode

| Feature / Characteristic | 🐍 Pydroid 3 | 📝 Acode | ⚡ ZABACODE v0.3.5 |
| :--- | :--- | :--- | :--- |
| **License Model** | Freemium / Paywall | Paid Play Store | **100% Free & Open-Source (GPLv3)** |
| **Ads & Telemetry** | Includes Ads & Trackers | Includes Analytics | **ZERO Telemetry & ZERO Ads** |
| **Python Execution Engine**| ✅ Native | ❌ Requires Termux | ✅ **Isolated Subprocess Sandbox** |
| **UI Editor Engine** | ⚠️ IDLE Style | ✅ Modern Ace/Monaco | ✅ **Adaptive Monaco + Native Light Engine** |
| **AI Assistant Built-in** | ❌ None | ❌ None | 🚀 **Multi-Provider AI + 1-Click Auto-Fix** |
| **Library Manager** | ✅ Precompiled Wheels | ❌ None | 🚀 **`zabapip` + PyPI Direct Wheel Extractor** |
| **Architecture Support** | 32-bit / 64-bit | - | ✅ **Universal Fat APK (ARMv7 + ARM64)** |

---

## 🚀 Quick Start & Installation

### Option 1: Download Pre-compiled APK (Recommended)
1. Visit the [GitHub Releases](https://github.com/muzape28-blip/ZABACODE/releases) page or the **Actions** tab.
2. Download `Zabacode-Universal-v0.3.5.apk`.
3. Install on your Android phone (Android 8.0 / API 26+).

### Option 2: Running Development Server Locally

```bash
# 1. Clone this repository
git clone https://github.com/muzape28-blip/ZABACODE.git
cd ZABACODE

# 2. Install dev dependencies
pip install -r requirements-dev.txt

# 3. Start Flask backend
python main.py

# 4. Open browser at http://127.0.0.1:5000
```

---

## 👥 Core Team & Contributors

<p align="left">
  <a href="https://github.com/muzape28-blip">
    <img src="https://github.com/muzape28-blip.png" width="60" height="60" style="border-radius:50%" alt="Zaqi">
  </a>
  &nbsp;&nbsp;
  <a href="https://arena.ai">
    <img src="https://arena.ai/favicon.ico" width="60" height="60" style="border-radius:50%" alt="Arena.ai Agent">
  </a>
</p>

* **[Zaqi (`muzape28-blip`)](https://github.com/muzape28-blip)** — *Creator, Lead Developer & Architect*
* **[Arena.ai Agent](https://arena.ai)** — *AI Co-Developer & Code Engineer*

---

## 📜 License & Freedom Statement

This program is free software: you can redistribute it and/or modify it under the terms of the **GNU General Public License (GPLv3)** as published by the Free Software Foundation.

```
Copyright (C) 2026 Zaqi (muzape28-blip) and ZABACODE Contributors.
ZABACODE comes with ABSOLUTELY NO WARRANTY.
```

---

<p align="center">
  <b>Built with ❤️ and 🔥 for the global open-source community.</b>
</p>
