# Security Policy & Architecture

## Reporting vulnerabilities

Please do **not** publish suspected vulnerabilities in public issues. Email `muzape28@gmail.com` with the subject:

```text
[SECURITY] ZABACODE vulnerability report
```

Include the affected version, reproduction steps, expected impact, and any proof of concept that can be shared safely.

## Security model in v1.0.0

### No local HTTP server

The Kivy-native application no longer runs the Flask/Waitress localhost server used by earlier releases. UI actions call Python functions directly, so there are no HTTP API routes or browser-visible session headers to expose.

### API-key storage

On Android, ZABACODE uses `EncryptedSharedPreferences` through Pyjnius when the Android keystore is available. If that facility is unavailable, keys are held in memory for the current app session and are not written to disk. This fallback means the user must re-enter a key after restarting the app; it is intentional and safer than persisting a weakly obfuscated secret.

### Package downloads

Package downloads retain normal HTTPS certificate verification. ZABACODE does not accept invalid certificates as a workaround for device or network failures. Direct wheel extraction validates every archive path before extraction and rejects paths outside `USER_PACKAGES_DIR`.

### Files and code execution

File names reject traversal sequences, hidden/system names, null bytes, and unsupported characters. Source files and execution output have size limits.

User Python runs in a separate subprocess with a 30-second timeout and process-group cleanup. This improves reliability but **is not a security sandbox**: user code can still have the permissions of the app process. Do not run untrusted code.

### Android backups

Android backup is disabled in the build configuration to reduce the chance that app-private data is copied through platform backups.

## Security checklist

- [x] Kivy-native app with no localhost HTTP server
- [x] Android keystore storage when available
- [x] In-memory-only fallback for API keys
- [x] TLS certificate verification for package and AI-provider HTTPS traffic
- [x] Wheel archive path validation
- [x] Filename validation and path-traversal protections
- [x] Source and output size limits
- [x] Subprocess timeout and process-group cleanup
- [x] Android backup disabled
