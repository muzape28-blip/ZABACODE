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

## Implemented Security Architecture (`v0.3.5`)

### 🔒 1. Dual-Layer Encrypted API Key Storage
* **Android Production Environment:** Menggunakan **Android Keystore System** via `EncryptedSharedPreferences` (`androidx.security.crypto`) melalui pembungkus `pyjnius`. Kunci API tidak pernah disimpan secara plaintext di storage HP.
* **Development / Desktop Mode:** Menggunakan obfuscated Fernet/XOR encryption berbasis hardware UUID lokal untuk memastikan `.zabacode_keys.json` terenkripsi dan tidak berupa teks polos.

### 🛡️ 2. Local Session Auth Token (`X-Zabacode-Token`)
* Setiap sesi server Flask menghasilkan token keamanan acak (`AUTH_TOKEN`) 128-bit yang terisolasi di internal app storage.
* Seluruh endpoint sensitif (`/api/run`, `/api/libraries/install`, `/api/files`, `/api/keys`) **diwajibkan membawa header `X-Zabacode-Token`**.
* Mencegah aplikasi/situs web jahat lain di perangkat yang sama mengakses API Zabacode.

### 🌐 3. Strict 127.0.0.1 Localhost Binding
* Server Flask/Waitress diikat (*bound*) secara eksklusif ke IP `127.0.0.1` (*loopback interface*).
* Server tidak terekspos ke jaringan Wi-Fi publik, menjamin isolasi total aplikasi.

### 📁 4. Sanitasi Nama File & Proteksi Path Traversal
* Penolakan eksplisit terhadap `..`, `/`, `\`, null bytes `\x00`, serta file tersembunyi yang diawali dengan titik `.` atau garis bawah `_` untuk mencegah pembacaan/penghapusan file kunci sistem.

---

## Security Audit Checklist
- [x] Process Subprocess Sandbox Execution
- [x] Localhost Only Binding (127.0.0.1)
- [x] Session Auth Token Header Verification
- [x] Android Keystore / Encrypted Preferences Integration
- [x] HTML Sanitization & XSS Prevention
- [x] Path Traversal Attack Prevention
