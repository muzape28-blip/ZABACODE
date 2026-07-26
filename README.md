<p align="center">
  <img src="assets/logo.png" alt="ZABACODE Logo" width="200" height="200">
</p>

<h1 align="center">⚡ ZABACODE ⚡</h1>

<p align="center">
  <b>The Uncompromising, Standalone Anti-Capitalist Mobile Python IDE & AI Code Assistant</b><br>
  <i>Offline-first, Zero Telemetry, 7 AI Providers + Zaba Oracle — Built for Android ARMv7 / ARM64</i>
</p>

<p align="center">
  <a href="https://github.com/muzape28-blip/ZABACODE/actions/workflows/build_apk.yml"><img src="https://github.com/muzape28-blip/ZABACODE/actions/workflows/build_apk.yml/badge.svg" alt="Build"></a>
  <a href="https://github.com/muzape28-blip/ZABACODE/actions/workflows/arena-integration.yml"><img src="https://github.com/muzape28-blip/ZABACODE/actions/workflows/arena-integration.yml/badge.svg" alt="Arena CI"></a>
  <a href="https://github.com/muzape28-blip/ZABACODE/releases"><img src="https://img.shields.io/badge/Release-v1.2.0--arena-39FF14.svg?style=flat&logo=android" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-GPLv3-blue.svg" alt="GPLv3"></a>
  <img src="https://img.shields.io/badge/Architecture-ARMv7%20|%20ARM64-FFB000.svg" alt="Arch">
  <img src="https://img.shields.io/badge/UI-WebView%20%2B%20Ace-147885.svg" alt="WebView">
  <img src="https://img.shields.io/badge/Providers-7%20%2B%20Oracle-FFB000.svg" alt="Providers">
  <img src="https://img.shields.io/badge/Telemetry-ZERO-brightgreen.svg" alt="Zero Telemetry">
  <img src="https://img.shields.io/badge/Arena-Integrated-8A2BE2.svg" alt="Arena Integrated">
</p>

---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ZABACODE v1.2.0-arena — WebView Shell + Modular Python Core              │
│  [ OK ] Ace Editor 1.32.4 Bundled (100% Offline, 45-60 FPS)               │
│  [ OK ] Modular Core Engine + Isolated Subprocess Runner (Timeout+PGID)  │
│  [ OK ] Android Keystore + Authenticated Key Vault (AES-GCM)             │
│  [ OK ] PyPI Wheel Extractor (Verified TLS + certifi + SHA-256)          │
│  [ OK ] 7 AI Providers: OpenRouter/Gemini/Groq/Mistral/DeepSeek/Ollama/Arena │
│  [ OK ] Zaba Oracle — Offline Code Intelligence (No Key, No Network)     │
│  [ OK ] Arena Integration — Offline-first, Zero Telemetry, Custom Endpoint│
│  [ OK ] Theme Engine (10 Themes: Tokyo Night, Catppuccin, Dracula...)    │
│  [ OK ] Plugin Marketplace (12+ Plugins, 8 Snippets, 5 Transform)         │
│  [ OK ] Security: CSP, X-Content-Type-Options, Loopback-Only Server      │
│  > WORKSPACE READY. HAPPY MOBILE CODING!                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏛️ Philosophy

**ZABACODE** — inspired by **Zabaniyah**, the uncompromising guardians.

In a mobile ecosystem full of ads, paywalls, and telemetry, ZABACODE is an anti-capitalist statement:

* **100% Free & GPLv3 Open Source**
* **Zero Ads, Zero Pop-ups**
* **Zero Telemetry / Zero Tracking**
* **Offline-first — works in airplane mode**

---

## 🚀 Key Features (v1.2.0-arena)

### 🔮 0. Zaba Oracle — Offline Code Intelligence

Other IDEs die without internet. ZABACODE doesn't.

* **Traceback Humanizer** — 20+ error families auto-translated to plain English with concrete fix, inline in terminal. Line numbers mapped to your editor (not prelude).
* **Offline Code Review** — AST-based detection: deep nesting, bare `except:`, mutable defaults, unreachable code, static `10/0`, security risks (`eval`, `exec`), missing docstrings, TODOs.
* **Graceful Fallback** — When cloud provider is rate-limited / no key / offline, Oracle answers. You never stare at a dead chat window.

```
🔮 Reached Past the End of a List          [OFFLINE]
   You asked for index 10 but list has only 3 items (0,1,2).
   Fix: Guard with `if i < len(my_list):` or use `for item in my_list:`
   Line 2
```

### ⚡ 1. Arena.ai Integration — 7th Provider (NEW in v1.2.0-arena)

Integrated directly from Arena Agent Mode workspace:

* **Offline-first, no API key needed** — branded as `⚡ ARENA INTEGRATION ACTIVE`
* **3 Models:**
  - `arena-offline-v1` → pure offline, fastest (<50ms)
  - `arena-oracle-enhanced` → Oracle + static analysis merged
  - `arena-custom-endpoint` → put URL in API Key field (`https://your-server/v1`) to route to your own LLM / Ollama
* **Uses verified TLS** via `get_ssl_context()` + `certifi` bundle, even for custom endpoints
* **Zero telemetry** — same promise as ZABACODE

> See `INTEGRATION_ARENA.md` and `tools/arena_sync.py` for full integration flow.

### 🛠️ 2. System Settings Dashboard

Clean sidebar:

* 🧩 Plugin & Theme Marketplace
* 📂 Open / Manage Files
* 💾 Save As File (.py)
* 🛠️ Settings & Preferences → full-screen dashboard:
  - 📦 Library Manager (zabapip)
  - 🚀 Offline Starter Kits (To-do, Safe Calculator, HTTP)
  - ⚙️ Editor Engine Switcher (Ace / Native fallback)
  - 🎨 Themes (10 presets)
  - 📺 CRT Scanlines Toggle
  - 🔑 AI API Keys (encrypted at-rest)

### 📦 3. Library Manager — Verified & Secure

**Not a bypass — verified security:**

* **Verified TLS** via `zabacode/core/net.py` + `certifi` + `openssl` (in `buildozer.spec`)
* **SHA-256 wheel verification** against PyPI's published hash — no MITM → RCE
* **Path validation** — archive members checked, no traversal
* **50+ libraries** cataloged with `tier` (runtime/buildtime) and `mode` (offline/online/hybrid)

### 📝 4. Ace Editor — Bundled Offline

* **Ace 1.32.4 bundled** in `assets/vendor/ace/` — no CDN, genuinely offline
* 45-60 FPS on mobile vs Monaco's 15-30 FPS
* Touch-friendly context menu (Undo, Redo, Find, Palette)
* Multi-tab with 500ms auto-save debounce, native fallback editor
* Symbol quick bar for mobile: `TAB : ( ) [ ] { } " ' = _ def return import`

### ⚙️ 5. Interactive Execution Engine — Isolated Subprocess

* **Isolated subprocess** with timeout (30s default) + process-group cleanup — no main thread blocking
* **Real-time streaming:** `/api/run/interactive/start|output|input|stop`
* **STDIN support:** type input while program runs, live char streaming
* **EXECUTE doubles as STOP** while process runs
* **Secure:** filename validation, size limits, no traversal, Android backup disabled

### 🧩 6. Transform Plugins (v1.1.0) — Offline AST

5 high-fidelity offline plugins via `PluginExecutor`:

* 🚀 **Auto-Import Optimizer:** comments out unused imports (AST)
* 🔍 **Duplicate Line Detector:** flags DRY violations
* ✍️ **Smart Comment Generator:** PEP-257 docstrings with Args/Returns
* 🎨 **Code Beautifier Pro:** PEP-8 spacing, preserves strings/comments
* 💡 **Type Hint Generator:** infers from defaults, adds `from typing import Any` if needed

Activate via Marketplace → instantly transforms active editor buffer.

---

## 📊 Comparison

| Feature | Pydroid 3 | Acode | ZABACODE v1.2.0-arena |
| :--- | :--- | :--- | :--- |
| **License** | Freemium / Paywall | Paid | **GPLv3 100% Free** |
| **Ads / Telemetry** | Ads + Trackers | Analytics | **ZERO** |
| **Python Engine** | Native | Needs Termux | **Isolated Subprocess Sandbox** |
| **UI Engine** | IDLE Style | Ace/Monaco | **WebView + Ace Bundled Offline** |
| **AI Providers** | None | None | **7 (OpenRouter/Gemini/Groq/Mistral/DeepSeek/Ollama/Arena) + Oracle** |
| **Offline AI** | None | None | **3 (Ollama, Arena, Oracle)** |
| **Library Manager** | Precompiled Wheels | None | **50+ Libs, Verified TLS + SHA-256** |
| **Themes** | Limited | Multiple | **10 incl. Tokyo Night, Catppuccin** |
| **Security** | Basic | Basic | **Loopback-only, Token Auth, Keystore AES-GCM, CSP, Verified TLS** |
| **Arch** | 32/64-bit | - | **Universal Fat APK ARMv7+ARM64** |

---

## 🏗️ Architecture

```
ZABACODE/
├── main.py → WebView shell entry
├── templates/index.html → Ace Editor + UI (offline)
├── assets/vendor/ace/ → Bundled Ace 1.32.4
├── zabacode/
│   ├── web_app.py → Flask + Waitress (127.0.0.1:5000, 4 threads, CSP headers)
│   ├── core/
│   │   ├── executor.py → Isolated subprocess, RLock-guarded InteractiveSession
│   │   ├── ai_provider.py → 7 providers (arena integrated)
│   │   ├── oracle.py → humanize_traceback, analyze_buffer, offline_reply
│   │   ├── net.py → shared verified SSL context (certifi)
│   │   ├── keystore.py → authenticated encryption at-rest
│   │   ├── security.py → AUTH_TOKEN, XOR + keystore
│   │   ├── file_manager.py → secure_filename, no traversal
│   │   ├── checker.py → syntax/bracket validation
│   │   └── paths.py
│   ├── lib_manager.py → PyPI extractor, SHA-256 verify
│   ├── plugins/ → registry + 5 transform implementations
│   └── themes/ → 10 theme definitions
├── files/ → user files (gitignored in APK)
├── tools/
│   ├── arena_sync.py → workspace sync + verification CLI
│   └── arena_integration_test.py → arena unit tests
└── .github/workflows/
    ├── build_apk.yml → APK build + lint + mypy + pytest
    └── arena-integration.yml → Arena CI (test 7 providers, TLS, offline)
```

---

## 🚀 Quick Start

### Option 1: Download APK (Recommended)
1. https://github.com/muzape28-blip/ZABACODE/releases
2. Download `Zabacode-1.2.0-arena.apk`
3. Install on Android 8.0+ (API 26+)

### Option 2: Dev Server (Desktop / Laptop)

```bash
git clone https://github.com/muzape28-blip/ZABACODE.git
cd ZABACODE

pip install -r requirements-dev.txt

# Run WebView server (Flask + Waitress @ 127.0.0.1:5000)
python main.py
# Open http://127.0.0.1:5000 — Ace editor loads offline

# Run tests — 132 + 5 arena = 137 passing
pytest test_main.py -v
pytest tools/arena_integration_test.py -v

# Verify Arena integration
python tools/arena_sync.py --verify --test-arena
```

### Option 3: Build APK Locally

```bash
pip install buildozer cython==0.29.33
buildozer -v android debug
# APK in bin/
```

`buildozer.spec` already includes `certifi`, `openssl` for TLS.

---

## 🔐 Security

* **Loopback-only server** (`127.0.0.1:5000`) + per-install `X-Zabacode-Token` (constant-time compare)
* **Android Keystore** (`EncryptedSharedPreferences` via Pyjnius) preferred, in-memory-only fallback
* **Verified TLS** for all HTTPS (AI providers + PyPI) via shared `get_ssl_context()` + certifi bundle — no `ssl._create_unverified_context()` anywhere
* **SHA-256 wheel verification** + archive path validation
* **CSP headers:** `default-src 'self'; frame-ancestors 'none';` + `X-Content-Type-Options: nosniff`
* **File protections:** no traversal, no dotfiles, no null bytes, size limits
* **Subprocess isolation:** timeout + PGID cleanup — not a sandbox, but reliable
* **Backup disabled:** `android:allowBackup="false"`

See `SECURITY.md` for policy + checklist.

---

## 📖 Docs & Roadmap

* `INTEGRATION_ARENA.md` → Full Arena integration guide (flow, offline/online, Oracle tie-in)
* `ZABACODEE.md` → Roadmap & Progress Tracker
* `CHANGELOG.md` → Version history
* `CONTRIBUTING.md` → How to contribute

**Current:** `v1.2.0-arena` (WebView + Arena Integrated)
**Next ideas:**
- [ ] Arena push-notify endpoint (`/api/arena/notify`)
- [ ] Voice TTS for Oracle
- [ ] File manager sync with Arena workspace FS
- [ ] More offline starter kits

---

## 👥 Core Team

* **[Zaqi (muzape28-blip)](https://github.com/muzape28-blip)** — Creator, Lead Architect
* **[Arena.ai Agent](https://arena.ai)** — AI Co-Developer, Arena Integration (7th provider)
* **Elicit AI** — Security hardening & release engineering

---

<p align="center"><b>Built with ❤️ and 🔥 for open-source, offline-first future.</b><br>ZABACODE x Arena.ai — Anti-capitalist, Fully Integrated, Zero Telemetry ⚡</p>
