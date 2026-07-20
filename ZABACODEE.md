# ZABACODE Roadmap & Progress Tracker

**Versi Sekarang:** `v0.3.0`  
**Lisensi:** GPL v3  
**Pengembang Utama:** Zaqi (`muzape28-blip`) & Contributors

---

## 🟩 Status Milestone & Rencana Realisasi

### 🟩 Milestone 1: Subprocess Engine Isolation (`v0.1.0` - `v0.3.0`) — SELESAI
* [x] `main.py` — Subprocess code execution isolation via `execute_code_isolated` dengan timeout 30 detik.
* [x] Automatic output capture (`stdout` vs `stderr`).
* [x] **Inline Graphic Plot Rendering:** Deteksi file gambar (`.png`, `.jpg`) baru hasil eksekusi (seperti grafik Matplotlib/PIL) dan tampilkan langsung di terminal output.

### 🟩 Milestone 2: Dedicated Library Manager Layer (`zabapip`) (`v0.3.0`) — SELESAI
* [x] Dipindahkan dari sidebar menjadi **Dedicated Full-Layer Overlay View** dengan Card Grid responsif.
* [x] Pencarian real-time dan filter kategori (`Web & API`, `Data & Sains`, `AI & Database`, `Media & Utils`).
* [x] **Custom PyPI Installer:** Pengguna dapat memasukkan nama package kustom PyPI mana saja untuk langsung di-install via `pip install --target`.
* [x] Pustaka `runtime` vs `buildtime` terintegrasi.

### 🟩 Milestone 3: Multi-Tab Adaptive Editor UI (`v0.3.0`) — SELESAI
* [x] **Multi-Tab File System:** Tab bar interaktif untuk berpindah dan membuat file Python secara bersamaan.
* [x] Adaptive Monaco Editor + Native Editor Fallback.
* [x] Theme Selector (`Retro Green`, `Solarized Dark`, `Dracula`) + CRT Scanlines Toggle.

### 🟩 Milestone 4: Updated Multi-Provider AI Engine — SELESAI
* [x] Model AI diperbarui ke versi mutakhir: OpenRouter (`qwen 2.5 coder free`), Gemini (`gemini-1.5-flash`), Groq (`llama-3.1-8b-instant`), Mistral (`codestral-latest`).
* [x] **`⚡ ZABA AI: BENERIN ERROR INI!`**: Auto-fix button langsung dari terminal error Traceback.

---

## 🔍 Quality Assurance & Build Configuration
* [x] `buildozer.spec`: Dukungan arsitektur ganda `armeabi-v7a` & `arm64-v8a` (Android API 34).
* [x] `test_main.py`: 17 Unit test lulus 100%.
* [x] `.github/workflows/build_apk.yml`: Otomatisasi CI/CD kompilasi APK.
