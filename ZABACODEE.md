# ZABACODE Roadmap & Progress Tracker

**Current Version:** `v1.2.0-arena` (WebView + Arena Integrated Edition)  
**License:** GPL v3  
**Lead:** Zaqi (`muzape28-blip`) + Arena.ai Agent + Contributors

---

## 🟩 Progress Log

### ⚡ v1.2.0-arena — Arena.ai Integration Edition (2026-07-26)

**New Provider: Arena (7th) — Offline-first, Zero Telemetry, Integrated from Arena Workspace**

* [x] **Arena Provider** (`zabacode/core/ai_provider.py`):
  - `ALLOWED_PROVIDERS` now 7: `openrouter, gemini, groq, mistral, deepseek, ollama, arena`
  - `call_arena()` — offline-first by default (no key, no network), uses `offline_reply()` + `analyze_buffer()` + Arena branding
  - Support custom endpoint: if API key is URL (`https://.../v1/chat/completions`), routes via verified TLS `get_ssl_context()`
  - `PROVIDER_INFO["arena"]` = `Arena.ai (Integrated)` — mode offline
* [x] **Frontend** (`templates/index.html`):
  - Dropdown `#ai-provider` now arena first: `⚡ arena (integrated)`
  - `PROVIDER_MODELS` adds 3 arena models: offline-v1, oracle-enhanced, custom-endpoint
  - `callAiWithFallback()` excludes `arena` & `ollama` from key requirement
  - Settings modal includes arena as FREE offline
* [x] **Backend** (`zabacode/web_app.py`):
  - `APP_VERSION = "1.2.0-arena"`
  - Offline providers bypass key check (`is_offline_provider`)
  - Health endpoint returns 7 providers
* [x] **CI** — New workflow `.github/workflows/arena-integration.yml`: integration-test, build-verification, security-scan
* [x] **Tools**: `tools/arena_sync.py` (status/verify/test-arena/prepare-push) + `tools/arena_integration_test.py` (5 tests)
* [x] **Docs**: `INTEGRATION_ARENA.md` + README overhaul
* [x] **Tests**: Fixed `TestTLSHardening` to be dynamic (counts providers), `TestVersion` allows 1.2.0-arena — 137 tests passing
* [x] **Pushed to main**: commits `37fe823` + `bee0e2a` on `origin/main`
* [x] **Removed ZMUX references** from README — ZMUX terminal independent concept postponed, not active in this version

### 🔒 v1.1.0 — Hardening & Zaba Oracle (2026-07-25)

**Major Security & Offline Intelligence Release**

* [x] **Zaba Oracle** (`zabacode/core/oracle.py`): offline code intelligence
  - `humanize_traceback()` — 20+ error families to plain English + fix
  - `analyze_buffer()` — AST review: deep nesting, mutable defaults, unreachable, static 10/0, security risk
  - `offline_reply()` — rule-based tsundere assistant, no key, no network
  - Endpoints: `/api/oracle/explain`, `/api/oracle/analyze`, auto fallback in `/api/ai/chat`
* [x] **TLS Hardening** — Fixed `CERTIFICATE_VERIFY_FAILED` across all 6 providers:
  - Added `certifi` + `openssl` to `buildozer.spec`
  - `zabacode/core/net.py` shared verified SSL context
  - Every `urlopen` passes `context=get_ssl_context()`
* [x] **Keystore** — `zabacode/core/keystore.py`: authenticated AES-GCM at-rest encryption, no hardcoded key
* [x] **Ace Bundled** — Ace 1.32.4 in `assets/vendor/ace/` — genuinely offline, no CDN
* [x] **Security Headers** — CSP `default-src 'self'`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`
* [x] **Fixes**: `/api/translations` 500, traceback line offset via `PRELUDE_LINE_COUNT`, `InteractiveSession` RLock guarded, Flask `static_url_path` pinned
* [x] **Cleanup**: Removed `zabacode/ui/` (1492 lines unreachable Kivy code)
* [x] **Tests**: 77 → 122 passing

### 🎨 v1.0.0 — WebView Shell + Modular Core (2026-07-21)

* [x] **WebView Shell Restoration** — Flask + Waitress on `127.0.0.1:5000`, Ace Editor
* [x] **Interactive Execution** — `/api/run/interactive/start|output|input|stop` with real-time streaming, STDIN via Enter, EXECUTE doubles as STOP
* [x] **Multi-Tab Editor** — auto-save debounce 500ms, native fallback
* [x] **Touch Context Menu** — floating trigger `•••` with Undo, Redo, Find, Palette
* [x] **Multi-Tab FS Manager** — secure filename, no traversal
* [x] **Theme Engine** — 10 themes (Retro, Dracula, Tokyo Night, Catppuccin Mocha, etc.)
* [x] **Plugin Marketplace** — 12+ plugins + 8 snippets + 5 transform plugins (v1.1.0)
* [x] **Library Manager** — 50+ libs with tier/mode, verified TLS + SHA-256
* [x] **AI Providers** — 6 providers (OpenRouter, Gemini, Groq, Mistral, DeepSeek, Ollama offline)
* [x] **Security**: `X-Zabacode-Token` auth, Android Keystore, CSP, path validation, subprocess timeout
* [x] **Dev Tooling**: ruff, mypy, pytest — 132 tests

### 🩹 Hotfix — WebView UI Restoration (2026-07-21)

* [x] Restored `templates/index.html` (was 0 bytes in PR #4)
* [x] Removed stale `zabacode_crash.log`, fixed `.gitignore`

### 📦 v0.3.5 and earlier (Pre v1.0)

* [x] Local Session Auth Token (`X-Zabacode-Token`)
* [x] Real Android Keystore Integration
* [x] Plugin & Theme Marketplace
* [x] PyPI direct extractor (now verified TLS, not bypass)
* [x] Monaco Mobile Soft Keyboard Focus → replaced by Ace touch handling
* [x] XSS HTML Sanitization

---

## 🚧 Postponed / Not Active (Removed from README)

* **ZMUX Independent Terminal**: The concept of a full Termux-like independent terminal with `zmux_bin/.shims/`, launcher alias injection, `noexec` bypass, and integrated Termux commands (`pkg`, `apt`, etc.) is **postponed**. It was documented in README v1.0 but removed now because:
  - Requires more Android-specific testing
  - Needs command branching design (Termux command tree) + POSIX compliance research
  - Current execution model is isolated subprocess sandbox — simpler, more secure, sufficient for Python IDE

  If/when ZMUX returns, it will be as `v2.0` major feature with its own spec in `docs/zmux-spec.md`, not mixed in main README.

---

## 📊 Version Map

| Version | Nickname | Core | AI Providers | Key Milestone |
| :--- | :--- | :--- | :--- | :--- |
| v0.3.5 | WebView Early | Flask + Monaco | 4 | Auth token, Keystore, Marketplace |
| v1.0.0 | WebView Modular | Flask + Ace Bundled | 6 + Oracle fallback | Multi-tab, Interactive exec, 10 themes |
| v1.1.0 | Hardening + Oracle | Flask + Ace + Oracle | 6 + Oracle offline | TLS fix, Keystore AES-GCM, CSP, Oracle full |
| **v1.2.0-arena** | **Arena Integrated** | **Flask + Ace + Oracle + Arena** | **7 + Oracle** | **Arena 7th provider offline-first, Arena CI, tools/arena_sync.py, README overhaul, ZMUX removed** |

---

## 🎯 Next (Ideas)

* [ ] Arena push-notify endpoint (`/api/arena/notify`) for workspace → Android
* [ ] Voice TTS for Oracle explanations
* [ ] File manager sync with Arena workspace FS
* [ ] More offline starter kits (argparse CLI, Flask mini, SQLite Todo)
* [ ] APK size optimization (Ace tree-shaking)
* [ ] Optional ZMUX v2 spec (when ready)

---

<p align="center"><b>v1.2.0-arena — ZABACODE x Arena.ai — Offline First, Fully Integrated</b></p>
