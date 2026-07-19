# ZABACODE

[![Build Status](https://github.com/muzape28-blip/ZABACODE/actions/workflows/build_apk.yml/badge.svg)](https://github.com/muzape28-blip/ZABACODE/actions)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

**Zabacode** adalah IDE Python mobile standalone untuk Android ARMv7 yang menggabungkan kesederhanaan **Pydroid** dengan detail & completeness **Acode** — plus AI assistant tsundere gratis. 100% open-source, anti-kapitalis (zero telemetry), bertujuan F-Droid.

```
┌─────────────────────────────────────────────────┐
│  ZABACODE v0.2.0                                │
│  [ OK ] python engine ready                     │
│  [ OK ] monaco editor loaded                    │
│  [ OK ] zabacode ai: standby (mulutnya pedas)   │
│  > ready_                                       │
└─────────────────────────────────────────────────┘
```

## Features

✅ **Milestone 1: Code Execution**
- Python code editor dengan Monaco Editor (syntax highlighting, auto-indent)
- Eksekusi code dalam isolated subprocess (tidak hang app saat infinite loop)
- Timeout protection (30 detik default)
- Real-time output dengan distinction stdout (mint) vs stderr (merah)

✅ **Milestone 2: Library Manager**
- 2-tier package system: `runtime` (pure Python, install langsung) vs `buildtime` (C-extension, rebuild APK)
- 15+ popular libraries (requests, beautifulsoup4, click, pillow, pandas, numpy, scipy, dll)
- Live install feedback (loading, success, error states)

✅ **Milestone 3: Enhanced UI**
- **Monaco Editor**: syntax highlighting, auto-complete, bracket matching, language support
- **File Manager**: Save/Open/Delete Python files ke internal storage
- **3 Theme Presets**: Retro Green, Solarized Dark, Dracula
- **Line:Col counter** ala Pydroid
- **Responsive sidebar** dengan Library Manager, AI status, Docs link

✅ **Milestone 4: Multi-Provider AI**
- **OpenRouter** (Qwen3 Coder, DeepSeek) — state-of-the-art code generation
- **Google Gemini** (1M context window) — perfect buat baca banyak file
- **Groq** (ultra-fast inference) — respons instan saat coding
- **Mistral Codestral** — khusus code generation & refactoring
- Auto-prompt API key dialog (symmetric encryption via Android Keystore)
- Context-sharing otomatis: code yang kebuka langsung attached ke chat

✅ **Security**
- Encrypted API key storage via Android Keystore (fallback plaintext di dev)
- Sandbox isolation: process execution terpisah, tidak akses root
- 100% local execution (offline mode supported)
- Zero telemetry

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

### Build APK

**Requirements:**
- Python 3.8+
- Java 11+ (buildozer perlu compile Android app)
- Android SDK/NDK (buildozer otomatis download kalau belum ada)

**Option 1: Local (tidak recommended, butuh resources gede)**
```bash
pip install buildozer cython
buildozer android debug
# APK ada di bin/zabacode-*.apk
```

**Option 2: GitHub Actions (recommended)**
```bash
# Push ke repo, Actions otomatis build APK
git push origin main

# APK available di Releases atau Artifacts
# Kalau push tag: otomatis release ke GitHub Releases
git tag v0.2.0
git push origin v0.2.0
```

## Configuration

### buildozer.spec
- Target: ARMv7 32-bit, Android API 26+ (Android 8+)
- Bootstrap: WebView (UI = HTML+JS dijalanin di WebView)
- Requirements: `python3,flask,requests,pyjnius`
- Dapat di-expand buat library lain (pandas, numpy, scipy = buildtime)

### AI Providers
Setup API keys di app sidebar → AI Assistant panel → copy-paste API key:

| Provider | Cost | Best For | Getting Key |
|----------|------|----------|-------------|
| **OpenRouter** | Free tier | Code generation (Qwen3 Coder) | https://openrouter.ai |
| **Gemini** | Free tier | Large context (1M tokens) | https://makersuite.google.com |
| **Groq** | Free tier | Ultra-fast inference | https://console.groq.com |
| **Mistral** | Free tier | Specialized code (Codestral) | https://console.mistral.ai |

Semua gratis! Kalau limit tercapai, tinggal switch provider.

## Roadmap

### FASE 0 ✅ Security
- [x] Encrypted API key storage (Android Keystore via pyjnius)
- [x] Process isolation (subprocess execution)
- [x] Zero telemetry

### FASE 1 ✅ Assets & Preparation
- [x] Frontend: Monaco Editor + sidebar
- [x] Backend: Flask HTTP routes
- [x] Library manifest: 15+ packages (runtime + buildtime)

### FASE 2 ✅ Core Technology
- [x] p4a/buildozer + WebView bootstrap
- [x] Python engine packaging (ARMv7)
- [x] HTTP API design

### FASE 3 ✅ UI & Features
- [x] Code execution dengan output terminal
- [x] Library Manager dengan install feedback
- [x] File Manager (Save/Open/Delete)
- [x] Theme selector (3 presets)
- [x] Monaco Editor integration

### FASE 4 ✅ AI Integration
- [x] Multi-provider AI chat
- [x] API key management (encrypted)
- [x] Context-sharing (code auto-attach)
- [x] System instruction (tsundere AI personality)

### FASE 5 🚀 Production & Release
- [ ] Security audit (pen-test sandbox)
- [ ] Hardware testing (real ARMv7 device)
- [ ] F-Droid submission
- [ ] GitHub Releases + CI/CD badge

## Testing Checklist

### Before Production:
- [ ] **Sandbox Security**: Run nakal script (`os.system()`, etc) → verify sandbox blocks
- [ ] **Offline Mode**: Matikan Wi-Fi → `/api/run` tetap jalan, AI chat offline (normal)
- [ ] **Stress Test**: Large loop (1M iterations) → monitor RAM, no crash
- [ ] **Timeout Test**: `while True: pass` → proses auto-kill setelah 30s
- [ ] **Library Install**: Runtime package (requests) → install via app successfully
- [ ] **AI Chat**: Send message → auto-prompt key → save encrypted → chat berjalan
- [ ] **File Manager**: Save code → Restart app → Open file → kode masih ada
- [ ] **Theme Switch**: Change theme → colors update instantly → saved ke localStorage
- [ ] **First Build**: `buildozer android debug` → cek error log, adjust spec kalau perlu

## Troubleshooting

### Build fails: "NDK not found"
```bash
# buildozer otomatis download NDK, tapi versi mungkin ga cocok
# Cek: ~/.buildozer/android/platform/android-ndk-*/
# Atau update buildozer.spec: android.ndk_api = 21
```

### Build hangs at "Compiling..."
Normal! Pertama kali compile Python buat ARMv7 butuh 30-60 menit (tergantung internet).
Kedua kali lebih cepat (cache).

### APK ga jalan di HP: "Application not installed"
- Pastiin HP punya ARMv7 support: `adb shell getprop ro.product.cpu.abi` → harus `armeabi-v7a`
- Cek Android version: perlu API 26+ (Android 8+)
- Lihat logcat: `adb logcat | grep zabacode`

### AI chat error: "API key invalid"
- Verify key di provider dashboard (mungkin expired)
- Delete file `.zabacode_keys_encrypted.json` → re-enter key

## Architecture

```
zabacode/
├── main.py                 Flask backend (300+ lines)
│   ├── Process isolation   subprocess execution + timeout
│   ├── Library Manager     2-tier (runtime vs buildtime)
│   ├── File Manager        Save/Open/Delete
│   ├── AI Chat             4 providers (OpenRouter, Gemini, Groq, Mistral)
│   ├── Theme Engine        3 presets (Retro, Solarized, Dracula)
│   └── Security            Encrypted keys (Android Keystore)
│
├── templates/index.html    Web UI (600+ lines)
│   ├── Monaco Editor       Syntax highlighting, auto-indent
│   ├── Sidebar             Library Manager, AI status, Docs
│   ├── File Manager        Dialog untuk save/open/delete
│   ├── Theme Selector      Dialog untuk 3 themes
│   ├── AI Chat Panel       Draggable FAB + chat interface
│   └── Output Terminal     Full-screen result view
│
├── buildozer.spec          APK config (Android ARMv7)
├── build_apk.yml           GitHub Actions CI/CD
└── README.md               This file
```

**Request flow:**
1. User ketik code di Monaco Editor
2. Press "EXEC" → JS kirim ke `/api/run`
3. Flask spawn subprocess → exec code → capture stdout/stderr
4. Balikin JSON hasil → JS render di full-screen terminal
5. User buka AI panel → ketik pertanyaan + code auto-attached
6. JS kirim ke `/api/ai/chat` → Flask call provider API
7. Response balikin → display di chat panel

**Data flow:**
```
User Input
    ↓
JavaScript (Frontend)
    ↓
Flask HTTP API (main.py)
    ↓
Python Subprocess (isolated code execution)
    ↓
Provider API (OpenRouter/Gemini/Groq/Mistral)
    ↓
Response back to UI
```

## Contributing

Kontribusi welcome! Areas:

1. **Library recipes**: Cek p4a recipes → tambah ke KNOWN_LIBRARIES
2. **UI improvements**: Monaco keybindings, theme customization, sidebar tabs
3. **AI providers**: Implementasi provider baru (Claude, LLaMA, dll)
4. **Testing**: Hardware testing (ARMv7 device), security audit
5. **Documentation**: Tulis guides, troubleshooting tips

## License

GNU General Public License v3.0 — lihat [LICENSE](LICENSE) file.

**TLDR:** Kode ini gratis, bisa dimodifikasi, tapi derivative works juga harus open-source.

---

## Acknowledgments

- **AI Assistance**: Claude, Gemini, Meta (code review & architecture suggestions)
- **Inspiration**: Pydroid (simplicity) + Acode (completeness)
- **Stack**: Flask, p4a, buildozer, Monaco Editor, android-crypto

---

**Status:** Production Ready (v0.2.0) — Ready untuk F-Droid submission setelah hardware testing & security audit.

**Next Steps:**
1. Test di real ARMv7 device (HP lama/budget 32-bit)
2. Sandbox security audit
3. F-Droid registration
4. Community feedback & iteration

**Chat dengan Zabacode AI:**
> "Aku asisten coding Zabacode, mulutku pedas tapi jago banget. Code lu baca otomatis, jadi ga usah copas-copasan. Ada yang perlu dibenahi atau dioptimasi? 😏"

---

*Made with ❤️ + zero telemetry for the Indonesian developer community* 🇮🇩
