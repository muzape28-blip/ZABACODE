# ZABACODE Roadmap & Progress Tracker

**Current Version:** `v1.2.0` (WebView + Oracle + Custom Endpoint)  
**License:** GPL v3  
**Lead:** Zaqi (`muzape28-blip`) & Contributors

---

## 🟩 Progress Log

### 🔧 v1.2.0 — Custom Endpoint + Cleanup (2026-07-26)

**Philosophy fix: Keep useful tool, remove permanent branding**

Based on community feedback (Claude review pointing out permanent branding pattern):

* [x] **Version cleanup**: `1.2.0-arena` → `1.2.0`, removed `__integration__ = "Arena.ai Agent Mode"` from `__init__.py` — version is project identity, not tool credit
* [x] **Provider refactor**: `arena` (offline re-branding of Oracle) → `custom` (neutral)
  - Removed redundant offline mode (was just `oracle_offline_reply()` + label "⚡ Arena")
  - Kept genuinely useful part: custom endpoint mode (URL as API key) → renamed `call_custom_endpoint()`, provider key `custom`, label neutral "🔧 Custom Endpoint (OpenAI-compatible)"
  - `ALLOWED_PROVIDERS` now: `openrouter, gemini, groq, mistral, deepseek, ollama, custom` (7 total)
  - `PROVIDER_INFO["custom"]` = Custom Endpoint, mode online, icon 🔧
* [x] **Frontend**: `templates/index.html` → dropdown `custom` instead of `arena`, `PROVIDER_MODELS` = custom-default, openai-compatible, ollama-compatible, settings modal neutral
* [x] **Backend**: `web_app.py` version 1.2.0, offline-only `ollama` (arena removed from offline list)
* [x] **CI**: Deleted `.github/workflows/arena-integration.yml` which gated build on word "arena" — moved useful security checks (no unverified SSL, Ace bundled, CSP, certifi, no CDN) into `build_apk.yml` as general checks without branding gate
* [x] **Docs**: Deleted `INTEGRATION_ARENA.md` (contained branding + credits), deleted `tools/arena_sync.py` + `tools/arena_integration_test.py` (arena-specific)
* [x] **README overhaul**: Removed Arena Integrated badge, Arena CI badge, removed Arena from boot box, removed `INTEGRATION_ARENA.md` references, removed Arena from Core Team credits — now only Zaqi + Contributors (community-owned)
* [x] **Philosophy preserved**: Tools help debug/review, identity stays with community — added explicit note in CONTRIBUTING: "cuma cek/fix bug, jangan nambahin fitur/branding/identitas baru tanpa nanya dulu"
* [x] **Mypy fix**: `ai_provider.py` mypy-clean (no None assignment to Callable, safe isinstance checks) — `Success: no issues found`
* [x] **Tests**: 132 passing (neutral)
* [x] **Zaba Oracle Auto-Fix**: Added local offline Auto-Fix support (`auto_fix_code`). When run exits with a traceback/SyntaxError, users get a `⚙️ Auto-Fix with Oracle` card showing a red/green line-by-line Diff, plus an `Apply Fix` button that modifies the editor and auto-saves. Fully covered with 8 new unit tests (138 tests total).

**Note:** Original Arena offline mode was Oracle re-branded — Oracle remains true offline brain, custom endpoint is optional online extension for self-hosting.

### ⚡ v1.2.0-arena — Arena Integration Attempt (2026-07-26) — SUPERSEDED by v1.2.0 cleanup

*History kept for transparency — this version had permanent branding that conflicted with anti-capitalist philosophy:*

* [x] Added `arena` provider with offline re-branding (later identified as duplicate of Oracle)
* [x] Added CI gate that failed if branding word "arena" removed
* [x] Added `__integration__` field and `-arena` suffix to version
* [x] Added `INTEGRATION_ARENA.md` with Arena in Credits

**→ All reverted/cleaned in v1.2.0 final**

### 🔒 v1.1.0 — Hardening & Zaba Oracle (2026-07-25)

* [x] **Zaba Oracle**: `humanize_traceback()` 20+ families, `analyze_buffer()` AST review, `offline_reply()` tsundere assistant, endpoints `/api/oracle/explain|analyze`
* [x] **TLS Hardening**: Fixed `CERTIFICATE_VERIFY_FAILED` — added `certifi`+`openssl` to spec, `net.py` shared verified context
* [x] **Keystore**: AES-GCM at-rest encryption, no hardcoded key
* [x] **Ace Bundled**: 1.32.4 genuinely offline
* [x] **Security Headers**: CSP, X-Content-Type-Options, Referrer-Policy
* [x] **Cleanup**: Removed `zabacode/ui/` Kivy
* [x] **Tests**: 77→122

### 🎨 v1.0.0 — WebView Shell + Modular Core (2026-07-21)

* [x] WebView shell, Ace Editor, multi-tab, touch context menu, interactive exec, theme engine, plugin marketplace, library manager, 6 providers + Oracle fallback, 132 tests
* [x] Hotfix: restored `templates/index.html` 0 bytes

### 📦 v0.3.5 and earlier

* [x] Auth token, Keystore, Marketplace, PyPI extractor (now verified TLS)

---

## 🚧 Postponed / Not Active

* **ZMUX Independent Terminal (v2)**: Postponed (Crucial Future Feature) — planned real shell persistent session (`ShellSession`) executing `/system/bin/sh` with concurrent locking (`RLock`), buffer limitations, custom path, and pip/pkg wrapper shims over `lib_manager.py` (offline, non-gimmick).
* **Arena offline re-branding**: Removed — Oracle is true offline intelligence, no need duplicate labeling

---

## 📊 Version Map

| Version | Nickname | Providers | Key Milestone |
| :--- | :--- | :--- | :--- |
| v0.3.5 | WebView Early | 4 | Auth, Keystore, Marketplace |
| v1.0.0 | WebView Modular | 6+Oracle | Ace bundled, Interactive exec, 10 themes |
| v1.1.0 | Hardening+Oracle | 6+Oracle | TLS fix, Keystore AES-GCM, Oracle full |
| v1.2.0-arena | Arena Attempt | 7+Oracle (with branding) | Superseded — branding conflict |
| **v1.2.0** | **Custom Endpoint** | **7 (6+custom)+Oracle** | **Neutral custom endpoint, cleanup, mypy fix, philosophy-aligned** |

---

## 🎯 Next

* [ ] Custom endpoint docs in `docs/custom-endpoint.md` (how to use with Ollama, vLLM, LocalAI)
* [ ] Voice TTS for Oracle
* [ ] More offline starter kits
* [ ] Optional ZMUX v2 spec

---

<p align="center"><b>v1.2.0 — Community-owned, Tools as Tools</b></p>
