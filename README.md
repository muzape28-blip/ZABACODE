<p align="center">
  <img src="assets/logo.png" alt="ZABACODE Logo" width="220" height="220">
</p>

<h1 align="center">⚡ ZABACODE ⚡</h1>

<p align="center">
  <b>Standalone Anti-Capitalist Mobile Python IDE & AI Code Assistant for Android</b>
</p>

<p align="center">
  <i>Combining the raw execution power of <b>Pydroid 3</b> with the detail, multi-tab elegance & UI control of <b>Acode</b> — now powered by a <b>WebView shell over a modular Python core</b> — 100% Free, Open Source, & Zero Telemetry.</i>
</p>

<p align="center">
  <a href="README_ID.md"><b>🇮🇩 Baca Dokumentasi Bahasa Indonesia</b></a>
</p>

<p align="center">
  <a href="https://github.com/muzape28-blip/ZABACODE/actions/workflows/build_apk.yml"><img src="https://github.com/muzape28-blip/ZABACODE/actions/workflows/build_apk.yml/badge.svg" alt="Build Status"></a>
  <a href="https://github.com/muzape28-blip/ZABACODE/releases"><img src="https://img.shields.io/badge/Release-v1.0.0-39FF14.svg?style=flat&logo=android" alt="Version"></a>
  <a href="https://www.gnu.org/licenses/gpl-3.0"><img src="https://img.shields.io/badge/License-GPLv3-blue.svg" alt="GPLv3 License"></a>
  <img src="https://img.shields.io/badge/Architecture-ARMv7%20%7C%20ARM64-FFB000.svg" alt="Architecture">
  <img src="https://img.shields.io/badge/UI-WebView%20Shell-147885.svg" alt="WebView Shell">
  <img src="https://img.shields.io/badge/Telemetry-ZERO-brightgreen.svg" alt="Zero Telemetry">
  <img src="https://img.shields.io/badge/Privacy-100%25%20Offline%20First-success.svg" alt="Offline First">
</p>

---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ZABACODE v1.0.0 — WebView Shell + Modular Python Core                    │
│  [ OK ] Local WebView UI Engine Active                                     │
│  [ OK ] Modular Core Engine Active                                         │
│  [ OK ] Subprocess Runner with Timeout & Process-Group Cleanup             │
│  [ OK ] Android Keystore API-Key Storage Active                             │
│  [ OK ] Direct PyPI Wheel Extractor with TLS Verification                  │
│  [ OK ] Multi-Provider AI Engine (6 Providers: OpenRouter/Gemini/Groq/    │
│         Mistral/DeepSeek/Ollama)                                           │
│  [ OK ] Multi-Language i18n Engine (2 Languages: ID/EN)       │
│  [ OK ] Theme Engine Active (10 Themes incl. Tokyo Night/Catppuccin)      │
│  [ OK ] Plugin Marketplace Active (12 Plugins, 8 Snippets)                │
│  [ OK ] Library Manager (50+ Libraries with Offline/Online Mode Tags)     │
│  > WORKSPACE READY. HAPPY CODING!_                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏛️ Lore & Philosophy

The name **ZABACODE** is inspired by **Zabaniyah** — the legendary guardian entities known for their uncompromising strength and vigilance. 

In a mobile software ecosystem overcrowded with invasive ads, aggressive paywalls, personal data mining (*telemetry*), and expensive subscriptions, **ZABACODE stands as an anti-capitalist statement**:
* **100% Free & Open-Source (GPLv3)**
* **Zero Banner Ads or Annoying Pop-ups**
* **Zero Telemetry / Zero Tracking**
* **Local-first code execution (offline core)**

---

## 🆕 v1.0.0: Modular core with a lightweight WebView shell

The UI uses a local WebView while the v1.0.0 modular Python core provides execution, file handling, package management, themes, plugins, and AI providers. This restores compatibility on constrained devices without discarding the refactored core.
- **Compatibility-first UI** — avoids the Kivy startup path that caused force closes on the current ARMv7 device
- **Modular core retained** — execution, security, file, package, and provider modules remain separate
- **Local-only server binding** — the shell binds to `127.0.0.1` only
- **Offline core** — editing and local execution work without a network connection

### 🧠 1. Subprocess Isolation & Auto `__file__` Resolution
* **Separate Process Runner:** Every Python script runs in a separate subprocess with a 30-second execution timeout. This is not a security sandbox; run only code you trust.
* **Automatic `__file__` Resolution:** Scripts are executed via `_active_run.py`, guaranteeing `Path(__file__)` **succeeds 100%**.

### 📦 2. Enhanced Library Manager (`zabapip`) — 50+ Libraries with Offline/Online Tags
* **Every library now has a `mode` tag:**
  - 🟢 **offline** — Works completely without internet (pure Python)
  - 🔵 **online** — Requires internet to function (API clients)
  - 🟡 **hybrid** — Core features offline, some features need internet
* **TLS verification:** Package downloads keep HTTPS certificate verification enabled. A certificate error stops installation instead of accepting an unsafe connection.
* **Categories:** Web & API, Data & Math, Database, AI & Automation, Utilities, Security, Media, Testing, Data Format, Networking

### 🤖 3. Multi-Provider AI — 6 Providers
* **OpenRouter** (🌐 online) — Multi-model access
* **Google Gemini** (🌐 online) — Gemini 1.5 Flash
* **Groq** (🌐 online) — Ultra-fast Llama 3.1
* **Mistral** (🌐 online) — Codestral
* **DeepSeek** (🌐 online) — DeepSeek Coder *(NEW)*
* **Ollama** (🖥️ **offline!**) — Local models, zero internet required *(NEW)*

### 🎨 4. Theme Engine — 10 Themes
* **Retro Green**, **Solarized Dark**, **Dracula**, **Cyberpunk Neon**, **Nord Arctic**, **Monokai Pro** *(carried over)*
* **Tokyo Night** *(NEW)*, **One Dark** *(NEW)*, **Gruvbox Dark** *(NEW)*, **Catppuccin Mocha** *(NEW)*

### 🌐 5. Multi-Language i18n — 2 Languages (ID & EN)
* 🇮🇩 **Bahasa Indonesia** (default)
* 🇬🇧 **English**

### 🧩 6. Plugin Marketplace — 12 Plugins + 8 Snippets
* **Core Plugins:** Auto-Code Formatter, Snippets Pack, Syntax Linter, Symbol Bar
* **New Plugins:** Code Minifier, JSON Formatter, Regex Tester, Color Picker, Markdown Preview, Code Timer/Profiler, ASCII Art Generator, TODO Manager

### ⚡ 7. Performance & Responsiveness
* Direct Python function calls (no HTTP overhead)
* Background threading for AI calls and library installations
* Kivy GPU-accelerated rendering
* Instant theme switching and language toggling

---

## 🏗️ Architecture & Data Flow

```
 ┌──────────────────────────────────────────────────────────┐
│              Local WebView UI Shell                       │
│    (HTML editor + themes + plugins + mobile controls)     │
└────────────────────────┬─────────────────────────────────┘
                         │ Direct Python Function Calls
┌────────────────────────▼─────────────────────────────────┐
│              ZABACODE Core Engine (Python)                │
│    (executor.py / security.py / checker.py / etc.)      │
└─────┬──────────────────┬──────────────────┬─────────────┘
      │                  │                  │
┌─────▼──────────┐ ┌────▼──────────────┐ ┌─▼──────────────┐
│ Subprocess     │ │ Direct PyPI       │ │ Multi-Provider  │
│ Code Execution │ │ Wheel Extractor   │ │ AI Chat Engine  │
│ (_active_run)  │ │ (zabapip)         │ │ (6 providers)   │
└────────────────┘ └──────────────────┘ └─────────────────┘
```

---

## 📊 Comparison: ZABACODE vs Pydroid 3 vs Acode

| Feature / Characteristic | 🐍 Pydroid 3 | 📝 Acode | ⚡ ZABACODE v1.0.0 |
| :--- | :--- | :--- | :--- |
| **License Model** | Freemium / Paywall | Paid Play Store | **100% Free & Open-Source (GPLv3)** |
| **Ads & Telemetry** | Includes Ads & Trackers | Includes Analytics | **ZERO Telemetry & ZERO Ads** |
| **Python Execution Engine**| ✅ Native | ❌ Requires Termux | ✅ **Isolated Subprocess Sandbox** |
| **UI Engine** | ⚠️ IDLE Style | ✅ Modern Ace/Monaco | ✅ **Local WebView shell** |
| **AI Assistant Built-in** | ❌ None | ❌ None | 🚀 **6 Providers + 1 Offline (Ollama)** |
| **Library Manager** | ✅ Precompiled Wheels | ❌ None | 🚀 **50+ Libs with Offline/Online Tags** |
| **Themes** | ⚠️ Limited | ✅ Multiple | 🚀 **10 Themes (Tokyo Night, Catppuccin, etc.)** |
| **Multi-Language UI** | ❌ None | ❌ None | 🚀 **2 Languages (ID/EN)** |
| **Architecture Support** | 32-bit / 64-bit | - | ✅ **Universal Fat APK (ARMv7 + ARM64)** |

---

## 🚀 Quick Start & Installation

### Option 1: Download Pre-compiled APK (Recommended)
1. Visit the [GitHub Releases](https://github.com/muzape28-blip/ZABACODE/releases) page or the **Actions** tab.
2. Download `Zabacode-Kivy-v1.0.0.apk`.
3. Install on your Android phone (Android 8.0 / API 26+).

### Option 2: Running Development Server Locally

```bash
# 1. Clone this repository
git clone https://github.com/muzape28-blip/ZABACODE.git
cd ZABACODE

# 2. Install dev dependencies
pip install -r requirements-dev.txt

# 3. Run Kivy app
python main.py

# 4. Run tests
pytest test_main.py -v
```

---

## 📁 Project Structure

```
ZABACODE/
├── main.py                          # Entry point
├── zabacode/
│   ├── __init__.py                  # Version & metadata
│   ├── core/
│   │   ├── paths.py                 # Path resolution
│   │   ├── security.py              # Auth, encryption, keystore
│   │   ├── executor.py              # Subprocess code execution
│   │   ├── checker.py               # Code syntax validation
│   │   ├── file_manager.py          # Safe file CRUD
│   │   └── ai_provider.py           # 6 AI provider handlers
│   ├── ui/
│   │   └── app.py                   # Main Kivy App & widgets
│   ├── themes/
│   │   └── definitions.py           # 10 theme color definitions
│   ├── i18n/
│   │   └── translations.py          # 6-language i18n engine
│   ├── plugins/
│   │   └── registry.py              # 12 plugins + 8 snippets
│   └── lib_manager.py               # 50+ library definitions + installer
├── assets/logo.png
├── buildozer.spec
├── test_main.py                     # 78 unit tests
└── ...
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
* **Elicit AI** — *Security hardening, code review & release-quality engineering*

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
