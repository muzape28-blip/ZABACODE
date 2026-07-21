# ZABACODE Roadmap & Progress Tracker

**Versi Sekarang:** `v0.3.5`  
**Lisensi:** GPL v3  
**Pengembang Utama:** Zaqi (`muzape28-blip`) & Contributors

---

## 🟩 Progress Log & Security Fixes

### 🟩 v0.3.5 Release Features:
* [x] **Local Session Auth Token Security (`X-Zabacode-Token`)**: Mengamankan seluruh endpoint lokal (`/api/run`, `/api/libraries/install`, `/api/files`, `/api/keys`) dengan token terenkripsi acak 128-bit.
* [x] **Real Android Keystore Integration**: Menggunakan `EncryptedSharedPreferences` via `pyjnius` di Android, dan Fernet/XOR obfuscated storage di desktop dev.
* [x] **Addon Plugin & Theme Marketplace (`#market-modal`)**: Marketplace fitur & tema melimpah (Auto-Formatter, Snippets, Linter, Symbol Bar, Cyberpunk, Nord, Monokai Pro) yang diakses via sidebar.
* [x] **PyPI Direct Extractor SSL Bypass**: Menambahkan `ssl.CERT_NONE` context agar ekstraksi Wheel dari PyPI berjalan 100% lancar tanpa error sertifikat SSL di Android.
* [x] **Fix Monaco Mobile Soft Keyboard Focus**: Mengatur `-webkit-user-select: text !important`, `domReadOnly: false`, dan tap listener agar keyboard HP langsung aktif saat Monaco diklik.
* [x] **XSS HTML Sanitization**: Menambahkan pembungkus `escapeHtml()` dan manipulasi DOM `textContent` untuk nama tab dan file.
* [x] **Dependency Completion**: Menambahkan `waitress>=2.1.2` ke `requirements-dev.txt`.
