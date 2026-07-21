# ZABACODE Roadmap & Progress Tracker

**Versi Sekarang:** `v0.3.4`  
**Lisensi:** GPL v3  
**Pengembang Utama:** Zaqi (`muzape28-blip`) & Contributors

---

## 🟩 Progress Log & Critical Fixes

### 🟩 v0.3.4 Release Features:
* [x] **Basmi Garis Putih Monaco / WebKit**: Diberlakukan rule CSS `-webkit-tap-highlight-color`, `border: none !important`, dan `renderLineHighlight: 'none'`.
* [x] **Sidebar Engine Selector**: Opsi satu-klik untuk switch antara Monaco Editor Engine dan Native Light Engine di sidebar.
* [x] **Fix `NameError: name '__file__' is not defined`**: Backend `main.py` menulis kode aktif ke `FILES_DIR / "_active_run.py"` sebelum dijalankan.
* [x] **Bypass `pip error (-11) / SIGSEGV`**: Direct PyPI Wheel Extractor via `zipfile.ZipFile`.
