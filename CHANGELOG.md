# Changelog

All notable changes to **ZABACODE** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] - 2026-07-26 — Custom Endpoint + Philosophy Cleanup (final)

### Philosophy
- **Goal:** Tools as tools, identity stays with community — per Claude review feedback
- **Problem in 1.2.0-arena:** Arena branding was permanently embedded: `__version__ = "1.2.0-arena"`, `__integration__` field, CI workflow `arena-integration.yml` that FAILED build if word "arena" removed, credits listing tool as co-author, roadmap toward deeper integration (push notify, FS sync)
- **Solution in 1.2.0 final:** Keep genuinely useful feature (custom endpoint), remove permanent branding

### Changed
- `zabacode/__init__.py`: `1.2.0-arena` → `1.2.0`, removed `__integration__ = "Arena.ai Agent Mode"`
- `zabacode/core/ai_provider.py`: `arena` → `custom`
  - Removed redundant offline mode (was just `oracle_offline_reply()` + label "⚡ Arena" — duplicate of Oracle, no new capability)
  - Kept useful: custom endpoint mode (URL as API key) → `call_custom_endpoint()`, provider `custom`, neutral label "🔧 Custom Endpoint (OpenAI-compatible)", verified TLS
  - `ALLOWED_PROVIDERS` still 7: openrouter, gemini, groq, mistral, deepseek, ollama, custom
  - `PROVIDER_INFO["custom"]` neutral, no branding
- `templates/index.html`: dropdown `arena` → `custom`, `PROVIDER_MODELS` neutral (custom-default, openai-compatible, ollama-compatible), offline check only `ollama` (not arena)
- `zabacode/web_app.py`: `1.2.0-arena` → `1.2.0`, offline provider only ollama
- `README.md`: Removed Arena Integrated badge + Arena CI badge, boot box now "7 AI Providers: .../Custom", Key Features 1 now "Custom Endpoint — Bring Your Own LLM" (neutral, no Arena branding), Core Team only Zaqi + Contributors, removed INTEGRATION_ARENA.md references, philosophy note "Community-owned — no single tool permanently branded"
- `ZABACODEE.md`: Rewrote to v1.2.0 neutral, added philosophy fix section, added Postponed section for ZMUX and arena offline re-branding, version map includes 1.2.0-arena superseded
- CI: Merged useful security checks from `arena-integration.yml` (no unverified SSL, Ace bundled, CSP, certifi, no CDN) into `build_apk.yml` as general checks without branding gate

### Removed
- `.github/workflows/arena-integration.yml` — deleted (was gating build on word "arena")
- `INTEGRATION_ARENA.md` — deleted (contained branding + credits)
- `tools/arena_sync.py` + `tools/arena_integration_test.py` — deleted (arena-specific)
- ZMUX docs already removed in previous commit, kept postponed note

### Fixed
- Mypy errors in previous `call_arena`: `Incompatible types in assignment (None vs Callable)`, `Function could always be true in boolean context`, `Any | object not indexable` — fixed by fallback function definitions matching exact oracle signatures, safe isinstance checks — now `Success: no issues found in 5 source files`
- Tests: 132 passing (neutral)

### Security
- Custom endpoint uses shared verified `get_ssl_context()` + certifi — no new attack surface
- Removal of arena CI gate reduces coupling, philosophy-aligned

### Notes
- This is the clean, philosophy-aligned final for v1.2.0 — useful tool kept, permanent branding removed

---

## [1.2.0-arena] - 2026-07-26 — Arena Integration + Repository Cleanup (SUPERSEDED)

### Added
- **Arena.ai Integration (7th Provider)** (`zabacode/core/ai_provider.py`):
  - `call_arena()` — offline-first integrated provider from Arena Agent Mode workspace
  - 3 models: `arena-offline-v1` (FREE, <50ms), `arena-oracle-enhanced` (Oracle + static analysis), `arena-custom-endpoint` (URL-as-API-key)
  - Uses shared verified TLS `get_ssl_context()` + certifi, supports custom OpenAI-compatible endpoints
  - `ALLOWED_PROVIDERS` now 7, `PROVIDER_INFO["arena"]` = `Arena.ai (Integrated)` offline mode
  - Frontend `templates/index.html`: arena as first default option, 3 models, bypass key check for offline providers
  - Backend `web_app.py`: `APP_VERSION = "1.2.0-arena"`, offline providers (`arena`, `ollama`) skip API key requirement
- **New CI Workflow** `.github/workflows/arena-integration.yml`: integration-test, build-verification (certifi/openssl, no unverified SSL, Ace bundled), security-scan (CSP headers, keystore), summary
- **Tools**: `tools/arena_sync.py` (status/verify/test-arena/prepare-push CLI) + `tools/arena_integration_test.py` (5 new tests for arena offline, custom endpoint fallback, analysis integration)
- **Docs**: `INTEGRATION_ARENA.md` (400+ lines, flow diagrams, offline/online table, Oracle tie-in) + README overhaul + ZABACODEE.md updated to v1.2.0-arena

### Fixed / Changed
- **README.md overhaul**: Removed ZMUX section entirely (ZMUX independent terminal concept postponed — requires Termux command branching design, `noexec` bypass research, and Android testing). Replaced with accurate **Interactive Execution Engine** description: isolated subprocess with timeout + PGID cleanup + real-time streaming (`/api/run/interactive/*`)
- **Library Manager doc**: Corrected from "Auto SSL-Bypass Fallback" (old insecure) to "Verified TLS + SHA-256" (current secure implementation in `net.py` + `lib_manager.py`)
- **Editor doc**: Replaced "Monaco WebView Focus" with "Ace Editor Bundled Offline" (Ace 1.32.4, 45-60 FPS, touch context menu)
- **Comparison table**: Updated from 6 providers to 7 + Oracle, 3 offline providers
- **Boot box**: Updated counts to 7 providers + Arena
- **Version badge**: `v1.0.0` → `v1.2.0-arena`
- **Quick Start**: Changed from "Run Kivy app" to "Run WebView server (Flask+Waitress @ 127.0.0.1:5000)" + added `arena_sync.py` verification steps
- **Test hardening**: `TestTLSHardening.test_all_ai_providers_use_shared_context` now dynamic (`len(ALLOWED_PROVIDERS)`) instead of hardcoded 6, allowing arena's 7th `urlopen` call
- **Version test**: `TestVersion` now accepts `1.2.0-arena` as valid

### Removed
- **ZMUX documentation**: Section "ZMUX Interactive Terminal (with Android noexec Bypass)" removed from README — code for ZMUX independent terminal was already removed earlier, but docs still mentioned `zmux_bin/.shims/`, launcher alias injection, `pkg`/`apt` Termux commands. Now documented as postponed in `ZABACODEE.md` with note for future `v2.0` spec in `docs/zmux-spec.md`

### Security
- No change to security model — Arena provider respects existing verified TLS context, CSP headers, loopback-only server, token auth, keystore AES-GCM
- ZMUX removal reduces attack surface (no custom shim directory + alias injection to audit)

### Notes
- Test suite: 132 → 137 passing (132 original + 5 arena)
- Pushed to `main` as `37fe823` + `bee0e2a`, also `feature/arena-integration` branch
- Requires APK rebuild to include Arena provider in release

---

## [1.1.0] — 2026-07-25 — Hardening & Zaba Oracle

### Added
- **Zaba Oracle** (`zabacode/core/oracle.py`): offline code intelligence — traceback humanizer (16+ error families), AST-based code review, and a rule-based assistant. Requires no API key and no network. New endpoints `/api/oracle/explain`, `/api/oracle/analyze`; crash explanations render inline in the terminal.
- AI chat now falls back to the Oracle when a provider is keyless or unreachable (opt out with `allow_offline: false`).
- `zabacode/core/net.py`: shared, certificate-verifying TLS context.
- `zabacode/core/keystore.py`: authenticated at-rest encryption for API keys.
- `/api/tls/status` diagnostic endpoint.
- Ace Editor 1.32.4 bundled in `assets/vendor/ace/` — the IDE is now genuinely offline.
- CSP, `X-Content-Type-Options` and `Referrer-Policy` headers.

### Fixed
- **All six AI providers failed with `CERTIFICATE_VERIFY_FAILED`** on Android: p4a ships no readable CA store. Added `certifi`/`openssl` to `buildozer.spec` and routed every request through a verified SSL context.
- `/api/translations` returned HTTP 500 (missing `zabacode.i18n`); replaced.
- Traceback line numbers were offset by the injected `SAFE_INPUT_PATCH` prelude.
- Race condition: `InteractiveSession` is now guarded by an `RLock` under `threads=4`.
- Flask served `assets/` at `/assets`, 404-ing every bundled asset; `static_url_path` pinned.

### Security
- Removed `ssl._create_unverified_context()` fallback in the PyPI installer (MITM → RCE); wheels are now verified against PyPI's published SHA-256.
- API keys no longer encrypted with a hardcoded source-code key.

### Removed
- `zabacode/ui/` — 1,492 lines of unreachable Kivy code superseded by the WebView shell.

### Notes
- Test suite: 77 → 122 passing. Requires an APK rebuild.

## [1.0.0] — 2026-07-21 — WebView Shell + Modular Core

### Added
- WebView Shell (Flask + Waitress @ 127.0.0.1:5000) + Ace Editor bundled offline
- Interactive Execution: `/api/run/interactive/start|output|input|stop` with real-time streaming, STDIN, EXECUTE as STOP
- Multi-Tab Editor with auto-save debounce 500ms, native fallback
- Touch Context Menu floating trigger `•••`
- Theme Engine (10 themes), Plugin Marketplace (12+ plugins, 8 snippets, 5 transform)
- Library Manager (50+ libs, tier/mode, verified TLS + SHA-256)
- 6 AI Providers + Oracle fallback
- Security: X-Zabacode-Token, Keystore, CSP, path validation, subprocess timeout
- Tests: 132 passing
