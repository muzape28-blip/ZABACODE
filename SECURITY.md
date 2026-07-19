# Security Policy

## Reporting Security Vulnerabilities

Kalau lu menemukan security vulnerability, **jangan** report di public issues.

Email ke: **muzape28@gmail.com** dengan subject line:
```
[SECURITY] ZABACODE vulnerability report
```

**Sertakan:**
1. Deskripsi vulnerability
2. Affected component/version
3. Steps to reproduce
4. Potential impact
5. Suggested fix (optional)

Kami akan:
- Acknowledge dalam 48 jam
- Investigate & assess severity
- Provide fix timeline
- Credit lu di release notes

## Security Features

### ✅ Implemented

1. **Process Isolation**
   - Code execution di subprocess terpisah
   - Tidak bisa crash app dengan infinite loop
   - Timeout protection (30 detik default)

2. **Encrypted Storage**
   - API keys disimpan di Android Keystore (encrypted)
   - Fallback plaintext hanya di dev mode
   - No hardcoded secrets

3. **Sandbox Validation**
   - File access restricted ke app-internal storage
   - Path traversal prevention
   - File extension validation (`.py` only)

4. **Zero Telemetry**
   - No analytics SDK (Firebase, etc)
   - No crash reporting
   - No ad networks
   - Completely offline capable

### ⚠️ Known Limitations

1. **Code Execution Sandbox**
   - Python code runs dalam app process
   - Tidak full OS-level isolation
   - **Recommendation:** Only run trusted code

2. **API Key Storage**
   - Android Keystore encryption optimal
   - Plaintext fallback di dev mode
   - **Recommendation:** Delete keys sebelum production

3. **Network Security**
   - Flask server bind ke `127.0.0.1` only
   - **Recommendation:** Use HTTPS buat production

## Before Production Release

- [ ] Security audit
- [ ] Penetration testing
- [ ] Dependency vulnerability scan
- [ ] Sandbox escape testing
- [ ] API key storage audit
- [ ] Code signing setup
- [ ] Privacy policy review

## Incident Response

Kalau ada security incident:
1. Investigate immediately
2. Contain the issue
3. Communicate with users
4. Release patch/workaround
5. Post-mortem & improvements

---

For questions: muzape28@gmail.com
