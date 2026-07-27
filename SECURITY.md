# Security Policy & Architecture — v1.2.0

## Reporting vulnerabilities

Please do **not** publish suspected vulnerabilities in public issues. Email `muzape28@gmail.com` with subject `[SECURITY] ZABACODE vulnerability report` and include a safe reproduction path.

## Security model — WebView shell

### Local-only server & token delivery (Issue #27)

The WebView shell uses Waitress bound to `127.0.0.1` (loopback-only). This reduces exposure but **is not a full app-private authorization boundary** — another local user/process on same device could potentially connect to loopback.

**Token handling:** The root HTML (`/`) embeds `AUTH_TOKEN` into inline JavaScript (`ZABACODE_TOKEN`) to allow the WebView UI to call sensitive APIs (`X-Zabacode-Token` header, constant-time compare via `hmac.compare_digest`). This token is per-installation, 128-bit hex, stored in `TOKEN_FILE` (`APP_DIR / ".zabacode_auth_token"`). Embedding in JS is necessary for WebView bootstrap but means token is visible in page source via loopback — we treat loopback as trust boundary, not as secret.

**Fixed port behavior:** Default port `5000`. If port 5000 is occupied (collision), server now attempts `5001`–`5010` with clear error message and recovery path. `run_webview_server()` detects `OSError` on bind and retries next port, logging attempt. Client (Android WebView) is configured via `p4a.port` in buildozer.spec — for desktop, user should check logs for actual port.

**Threat model:** Loopback + token protects against remote network attackers, but local unprivileged apps on same device could sniff loopback traffic on rooted devices or via `netstat`. This is documented as explicit limitation — not claimed as OS-level sandbox.

### API keys — two storage paths (Issue #19, #25)

**Path 1 — Android Keystore (preferred):**
- Uses AndroidX `EncryptedSharedPreferences` with `MasterKey.AES256_GCM`
- Keys stored as `PrefKeyEncryptionScheme.AES256_SIV` + `PrefValueEncryptionScheme.AES256_GCM`
- Provider list is now centralized via `ALLOWED_PROVIDERS` from `ai_provider.py` (includes `custom`) — previously only 6 providers were read, missing `custom` (#19 fixed)
- If keystore returns any keys, we now merge missing providers from encrypted file fallback to avoid losing `custom` on upgraded installs

**Path 2 — Fallback encrypted file (desktop / no Keystore):**
- **Not memory-only** — contrary to old docs, fallback **persists locally** in `KEYS_FILE` (`APP_DIR / ".zabacode_keys_encrypted.json"` or `.zabacode_keys_encrypted.json` depending on platform), with `chmod 600`
- **Construction:** `keystore.py` uses HMAC-derived stream cipher (HKDF from random master secret in `.zabacode_master_key`) with encrypt-then-MAC (HMAC-SHA256), **not AES-GCM** as previously documented. The master key file itself is random per-install, `chmod 600`, gitignored
- **Rooted device limitation:** On rooted devices, both Android Keystore and file-based fallback can be extracted — we document this explicitly, not hide
- **Backup:** Android backup disabled (`android:allow_backup = False`) to reduce copying app-private data via platform backups

**Custom Endpoint credential handling (Issue #24):**
- Previously Custom Endpoint URL was stored in API-key field accepting any `http://` or `https://`, sending editor context in cleartext if HTTP
- Now: Separate `endpoint_url` field (preferred) + optional credential, URL parsed/validated (must be http/https), default to HTTPS, explicit warning for HTTP
- UI shows destination and transport security before sending: if URL starts with `http://`, toast warns "⚠️ HTTP cleartext: code context will be sent unencrypted, use https:// for privacy. Allowed for loopback/private networks only."
- Backend validates URL via `startswith("http://") or "https://"` and rejects otherwise with `invalid_url` code

### Package downloads — verified TLS (Issue #22)

**Direct wheel path:** Uses verified TLS (`get_ssl_context()` + certifi bundle) + SHA-256 integrity check against PyPI's published digest + archive path validation (no traversal outside `USER_PACKAGES_DIR`).

**Fallback pip path:** Previously invoked `pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org` which **disables TLS certificate verification** for those hosts — conflicting with verified-TLS model. Fixed in v1.2.0: **removed `--trusted-host` flags**, retains verified TLS. If pip fails due to certificate, error message includes `TLS_HELP_MESSAGE` explaining CA-bundle remediation (install certifi, update system certs, check date/time), not bypass.

### Files and code execution (Issue #18, #20)

**Path resolution (Issue #20):**
- On Android: `APP_DIR` from `ANDROID_PRIVATE` env or Kivy `getFilesDir()`, `FILES_DIR = APP_DIR / "files"` but with deduplication to avoid `files/files` double nesting
- On Desktop fallback: `APP_DIR = project root` (where `main.py` lives), `FILES_DIR = project_root / "files"` — matches documentation "files/ at project root", not `zabacode/files/`
- All runtime dirs (`files/`, `zabacode/files/`, `cache/`, `zabacode/cache/`, `logs/`, `zabacode/logs/`, `user_packages/`, `**/_active_run.py`) are now gitignored — runtime files cannot appear in `git status` by default
- Tests verify path policy: `FILES_DIR` is under project root when no Android env, and `.gitignore` contains required entries

**Execution bounds (Issue #18):**
- Normal runner: 512 KiB source limit, output truncated at 256 KiB
- Interactive runner (previously unbounded): now enforces `MAX_CODE_BYTES` check (400 response if oversized), bounded queue `MAX_INTERACTIVE_QUEUE=10000`, bounded total chars `MAX_OUTPUT_CHARS`, `output_truncated` flag surfaced to UI, max duration `120s`, inactivity timeout `60s`, input size bound 8KB

### Privacy — Local drafts in WebView localStorage (Issue #21)

**Problem:** `saveTabsToStorage()` serializes complete `tabs` (including unsaved editor contents) to `localStorage` — can persist credentials, proprietary code.

**Fix:**
- **Disclosure:** Settings → Privacy card explains: stored in `localStorage` keys `zabacode-tabs` + `zabacode-active-tab-id`, device-only, not server, not encrypted, plain text
- **Opt-in/out:** Toggle `zabacode-persist-drafts` localStorage flag — `true` (default for backward compat, disclosed) or `false` (private/no-persistence mode, only in memory)
- **Clear:** One-click "Clear Local Drafts" button removes both keys from this device
- **Quota handling:** If `QuotaExceededError`, clear oldest drafts and toast
- **Documentation:** This SECURITY.md section + README + in-app status text

### JSON validation (Issue #23)

All authenticated JSON routes now require JSON object (not array/primitive) via `_get_json_payload()` helper. Invalid shapes return 400 with `code: invalid_json_type` instead of 500. Each field validated for type and bounds (e.g., `name` must be string, not `7`; `provider` must be string, not `{}`; `stdin_data` must be string; `allow_offline` must be boolean; `endpoint_url` must be http/https URL). `MAX_CODE_BYTES` enforced early with 413. Negative tests cover every JSON route.

### Build inputs locking (Issue #26)

- **Floating bounds:** Previously `requirements-dev.txt` used `flask>=2.3.3` etc., CI installed latest Buildozer/Ruff/Mypy/Pytest via mutable tags `actions/checkout@v4`, `setup-python@v5`
- **Fix:** Added `requirements.lock` (pip-compile style) with pinned hashes, pinned GitHub Actions to commit SHAs (not tags), added `tools/check.sh` local command mirroring CI (ruff critical + full non-blocking + mypy on 5 core files including ai_provider + pytest), documented which findings are blocking vs non-blocking
- **Reproducibility:** Fresh env can `pip install -r requirements.lock` and run `./tools/check.sh` to reproduce CI gate locally

### Android

Android backup disabled, permissions only INTERNET, adaptive icon background `#050806` + foreground `logo.png` (512x512 optimized), presplash `presplash.png` + color `#050806` (fixes white/purple default loading).

## Security checklist (for v1.2.0)

- [x] Loopback-only WebView server with ephemeral port fallback (5000→5010) and clear recovery log
- [x] Token-protected sensitive routes with constant-time compare, token exposure documented as loopback trust boundary
- [x] Android keystore storage when available, centralized provider list including custom
- [x] Fallback encrypted file persistence documented accurately (HMAC-derived stream cipher encrypt-then-MAC, not AES-GCM, chmod 600)
- [x] TLS certificate verification for package and AI-provider HTTPS traffic, no trusted-host bypass
- [x] Wheel archive path validation + SHA-256 integrity
- [x] Filename validation and path-traversal protections
- [x] Source and output size limits for both normal and interactive runners, bounded queue, duration/inactivity timeouts
- [x] Subprocess timeout and process-group cleanup
- [x] Android backup disabled
- [x] Privacy controls for localStorage drafts: opt-in/out, clear, disclosure, plain-text warning
- [x] JSON schema validation for all routes, no 500 on invalid types/shapes
- [x] Custom Endpoint URL separated from credential, URL validation, cleartext HTTP explicit warning
- [x] Build inputs locked, Actions pinned, local check command
