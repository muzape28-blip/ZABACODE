# Security Policy & Architecture

## Reporting Security Vulnerabilities

Jika Anda menemukan kerentanan keamanan, mohon **tidak** mempublikasikannya di public issues.

Kirimkan email ke: **muzape28@gmail.com** dengan subjek:
```
[SECURITY] ZABACODE vulnerability report
```

### Penanganan:
- Konfirmasi laporan dalam 24-48 jam.
- Penilaian dampak dan pembuatan perbaikan (*patch*).
- Kredit nama pelapor di *release notes*.

---

## Implemented Security Architecture (`v1.0.0`)

### 🔒 1. No Exposed HTTP Server (Kivy Native)
* **v1.0.0 eliminates the Flask/Waitress HTTP server entirely.** All backend operations are direct Python function calls within the same process.
* **No localhost binding risk** — there is no network-facing server to exploit.
* This is a significant security improvement over v0.3.5 which bound a Flask server to 127.0.0.1:5000.

### 🛡️ 2. Dual-Layer Encrypted API Key Storage
* **Android Production Environment:** Menggunakan **Android Keystore System** via `EncryptedSharedPreferences` (`androidx.security.crypto`) melalui pembungkus `pyjnius`. Kunci API tidak pernah disimpan secara plaintext di storage HP.
* **Development / Desktop Mode:** Menggunakan obfuscated XOR-Base64 encryption berbasis hardware UUID lokal untuk memastikan `.zabacode_keys.json` terenkripsi dan tidak berupa teks polos.

### 🔐 3. Local Session Auth Token
* Setiap sesi menghasilkan token keamanan acak (`AUTH_TOKEN`) 128-bit yang terisolasi di internal app storage.
* Token digunakan untuk enkripsi kunci API (XOR cipher key).
* Tanpa web server, token tidak lagi diekspos melalui HTTP headers, meningkatkan keamanan.

### 📁 4. Sanitasi Nama File & Proteksi Path Traversal
* Penolakan eksplisit terhadap `..`, `/`, `\\`, null bytes `\\x00`, serta file tersembunyi yang diawali dengan titik `.` atau garis bawah `_`.
* Validasi regex: hanya alphanumeric, dash, underscore, dan dot yang diizinkan.
* Null byte injection prevention.
* Auto-append `.py` extension.

### 🧩 5. Wheel Archive Path Validation
* PyPI Direct Wheel Extractor memvalidasi setiap path di dalam wheel archive.
* Jika path resolve ke luar `USER_PACKAGES_DIR`, instalasi ditolak (mencegah zip slip attack).

### 🔄 6. Subprocess Isolation
* User code execution berjalan di subprocess terpisah dengan timeout 30s.
* `start_new_session=True` memastikan process group killing saat timeout.
* `PYTHONNOUSERSITE=1` mencegah akses ke user site-packages yang tidak diizinkan.
* `__file__` resolution via `_active_run.py` temporary script.

---

## Security Audit Checklist
- [x] No Exposed HTTP Server (Kivy native, no Flask/Waitress)
- [x] Process Subprocess Sandbox Execution
- [x] Dual-Layer Encrypted API Key Storage (Keystore + XOR file)
- [x] Session Auth Token for Key Encryption
- [x] Path Traversal Attack Prevention
- [x] Null Byte Injection Prevention
- [x] Wheel Archive Path Validation (zip slip prevention)
- [x] Filename Validation with Regex
- [x] Code Size Limits (512KB max)
- [x] Output Truncation (256KB max)
