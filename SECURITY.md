# Security Policy & Architecture

## Reporting vulnerabilities

Please do **not** publish suspected vulnerabilities in public issues. Email `muzape28@gmail.com` with subject `[SECURITY] ZABACODE vulnerability report` and include a safe reproduction path.

## Security model in v1.0.0 WebView shell

### Local-only WebView server

The WebView shell uses Waitress bound only to `127.0.0.1:5000`. Sensitive routes require a per-installation `X-Zabacode-Token`; comparisons use a constant-time check. This is a local UI boundary, not a substitute for an OS sandbox.

### API keys

Android Keystore (`EncryptedSharedPreferences` through Pyjnius) is preferred. If unavailable, keys remain only in memory for the app session and are not written to disk.

### Package downloads

Package downloads retain normal HTTPS certificate verification. ZABACODE does not accept invalid certificates as a workaround. Direct wheel extraction validates archive paths before extraction and rejects paths outside `USER_PACKAGES_DIR`.

### Files and code execution

File names reject traversal sequences, hidden/system names, null bytes, and unsupported characters. Source files and execution output have size limits.

User Python runs in a separate subprocess with a 30-second timeout and process-group cleanup. This improves reliability but **is not a security sandbox**: user code still has the permissions of the app process. Do not run untrusted code.

### Android backups

Android backup is disabled to reduce the chance that app-private data is copied through platform backups.

## Security checklist

- [x] Loopback-only WebView server
- [x] Token-protected sensitive routes
- [x] Android keystore storage when available
- [x] In-memory-only fallback for API keys
- [x] TLS certificate verification for package and AI-provider HTTPS traffic
- [x] Wheel archive path validation
- [x] Filename validation and path-traversal protections
- [x] Source and output size limits
- [x] Subprocess timeout and process-group cleanup
- [x] Android backup disabled
