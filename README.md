<p align="center">
  <img src="assets/logo.png" alt="ZABACODE Logo" width="220" height="220">
</p>

<h1 align="center">⚡ ZABACODE ⚡</h1>

<p align="center">
  <b>The Uncompromising, Standalone Anti-Capitalist Mobile Python IDE & AI Code Assistant for Android</b>
</p>

<p align="center">
  <i>Combining the raw execution power of <b>Pydroid 3</b> with the detail, multi-tab elegance & UI control of <b>Acode</b> — powered by a <b>WebView shell over a modular Python core</b> — 100% Free, Open Source, & Zero Telemetry.</i>
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
│  ZABACODE — WebView Shell + Modular Python Core                           │
│  [ OK ] Local WebView UI Engine Active                                     │
│  [ OK ] Modular Core Engine Active                                         │
│  [ OK ] Subprocess Runner with Timeout & Process-Group Cleanup             │
│  [ OK ] Android Keystore API-Key Storage Active                             │
│  [ OK ] Direct PyPI Wheel Extractor (Auto-SSL Bypass Fallback Enabled!)    │
│  [ OK ] Multi-Provider AI Engine (6 Providers: OpenRouter/Gemini/Groq)     │
│  [ OK ] Universal English Language Engine Active                           │
│  [ OK ] Theme Engine Active (10 Themes incl. Tokyo Night/Catppuccin)      │
│  [ OK ] Plugin Marketplace Active (12 Plugins, 8 Snippets)                │
│  [ OK ] System Settings Dashboard (Clean Sidebar, Fast Controls)           │
│  > WORKSPACE READY. HAPPY MOBILE CODING!_                                  │
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

## 🚀 Key Features

### 🛠️ 1. All-New System Settings Dashboard
The sidebar has been redesigned to be ultra-clean, containing only:
* 🧩 **Plugin & Theme Marketplace**
* 📂 **Open / Manage Files**
* 💾 **Save As File (.py)**
* 🛠️ **Settings & Preferences**
* 📖 **Docs & Roadmap**

Tapping **Settings & Preferences** opens a gorgeous, full-screen cyber-hacker dashboard where you can easily toggle and configure:
* 📦 **Library Manager (zabapip)**
* 🚀 **Offline Starter Kits**
* ⚙️ **Editor Engine Selector (Monaco online / Native offline)**
* 🎨 **UI Themes (10 presets)**
* 📺 **CRT Scanline Effects**

### 📦 2. Library Manager (`zabapip`) with SSL/TLS Bypass Fallbacks
Tired of certificate installation failures on Android? So are we!
* **Auto SSL-Bypass Fallback:** If your device lacks updated root CA certificates (causing SSL verify failures), the installer automatically falls back to an unverified SSL context to ensure downloads *always* succeed.
* **Friendly Error Logs:** If installation fails, detailed logs are captured and presented in a clean, user-friendly pop-up dialog.
* **Pip Trusted Hosts:** Pip subprocess runs with `--trusted-host` configurations out of the box.

### ⚙️ 3. Seamless Monaco WebView Focus
* Removed non-standard CSS touch-action constraints that caused mobile WebView keyboards to lock.
* Added deterministic responsive touch event handlers so clicking or touching the Monaco container instantly focuses the hidden cursor input and triggers the software keyboard flawlessly.
* Graceful network check: Switching to Monaco editor is disabled when offline to prevent empty/blank screen lockouts.

### 🧮 4. Safe Calculator with Natural-Law Error Handling
Our **Safe Calculator** Starter Kit is completely updated in English! If you attempt to divide by zero, instead of a raw traceback crash, it returns a fun, philosophically correct response:
`"Division by zero is a violation of natural law"`!

---

## 📊 Comparison: ZABACODE vs Pydroid 3 vs Acode

| Feature / Characteristic | 🐍 Pydroid 3 | 📝 Acode | ⚡ ZABACODE |
| :--- | :--- | :--- | :--- |
| **License Model** | Freemium / Paywall | Paid Play Store | **100% Free & Open-Source (GPLv3)** |
| **Ads & Telemetry** | Includes Ads & Trackers | Includes Analytics | **ZERO Telemetry & ZERO Ads** |
| **Python Execution Engine**| ✅ Native | ❌ Requires Termux | ✅ **Isolated Subprocess Sandbox** |
| **UI Engine** | ⚠️ IDLE Style | ✅ Modern Ace/Monaco | ✅ **Local WebView shell** |
| **AI Assistant Built-in** | ❌ None | ❌ None | 🚀 **6 Providers + 1 Offline (Ollama)** |
| **Library Manager** | ✅ Precompiled Wheels | ❌ None | 🚀 **50+ Libs with Auto-SSL Bypass** |
| **Themes** | ⚠️ Limited | ✅ Multiple | 🚀 **10 Themes (Tokyo Night, Catppuccin, etc.)** |
| **Multi-Language UI** | ❌ None | ❌ None | 🚀 **Streamlined English Only (No Lag!)** |
| **Architecture Support** | 32-bit / 64-bit | - | ✅ **Universal Fat APK (ARMv7 + ARM64)** |

---

## 🚀 Quick Start & Installation

### Option 1: Download Pre-compiled APK (Recommended)
1. Visit the [GitHub Releases](https://github.com/muzape28-blip/ZABACODE/releases) page.
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

## 👥 Core Team & Contributors

* **[Zaqi (`muzape28-blip`)](https://github.com/muzape28-blip)** — *Creator, Lead Developer & Architect*
* **[Arena.ai Agent](https://arena.ai)** — *AI Co-Developer & Code Engineer*
* **Elicit AI** — *Security hardening, code review & release-quality engineering*

---

<p align="center">
  <b>Built with ❤️ and 🔥 for the global open-source community.</b>
</p>
