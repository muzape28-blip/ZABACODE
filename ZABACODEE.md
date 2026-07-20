# ZABACODE Roadmap & Progress Tracker

**Versi Sekarang:** `v0.3.3`  
**Lisensi:** GPL v3  
**Pengembang Utama:** Zaqi (`muzape28-blip`) & Contributors

---

## 🟩 Progress Log & Critical Fixes

### 🟩 v0.3.3 Release Features:
* [x] **Fix `NameError: name '__file__' is not defined`**: Backend `main.py` menulis kode aktif ke `FILES_DIR / "_active_run.py"` sebelum dijalankan oleh interpreter Python.
* [x] **Bypass `pip error (-11) / SIGSEGV`**: Penambahan `_fallback_pypi_download()` yang memanfaatkan PyPI JSON API + `zipfile.ZipFile` untuk mengunduh pure python wheel langsung tanpa C-compilation.
* [x] **Fix Layout Reset / Reappearing White Bar**: Mengubah link Docs & Roadmap menjadi Modal internal agar WebView tidak pernah berpindah URL, dan menonaktifkan `renderLineHighlight` pada Monaco Editor.
* [x] **Strict Localhost Security**: Binding `127.0.0.1` menjamin server isolasi lokal tidak terekspos di Wi-Fi publik.
