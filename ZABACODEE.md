# 🚀 ZABACODE PROJECT ROADMAP
> **Codename:** Zabacode.apk  (gabungan antara simplenya dan lengkapnya fungsi pydroid dan kelengkapan,rinci,detail seperti acode)
> **Concept:** Standalone Anti-Capitalist Android Python IDE (Acode UI + Internal Python Engine + ARMv7 Compatibility Layer + Tsundere AI Assistant)
> **License:** 100% Free & Open-Source (F-Droid Goal)
> **Arsitektur (v2):** python-for-android (p4a) + WebView-Flask bootstrap. Gantiin rencana awal Flutter + `Process.start()` binary Termux, karena binary Termux ke-hardcode buat package `com.termux` sendiri (ga bisa asal dipake app lain), dan p4a udah nyelesein masalah ini secara resmi lewat cross-compile khusus per-app. Detail histori keputusan ada di FASE 2.

---

## 🛡️ FASE 0: SECURE DATA & ARCHITECTURE SPECIFICATION
*Pondasi keamanan lokal dan arsitektur data terisolasi.*

*   **Sandbox Isolation:** Semua binary Python, library, dan script user wajib disimpan di direktori internal privat aplikasi (dikelola otomatis sama p4a saat build/first-run). Dilarang menggunakan External Storage umum demi mencegah pencurian kode oleh aplikasi lain.
*   **Encrypted Storage:** API Key (Google Gemini, dan provider gratis seperti OpenRouter/Groq — lihat poin di bawah) untuk AI Assistant wajib disimpan terenkripsi. **STATUS SEKARANG:** starter code (`main.py`) masih nyimpen plaintext JSON demi kecepatan Milestone 1 — ada `TODO KEAMANAN` eksplisit di kodenya. **WAJIB** diganti ke Android Keystore (lewat `pyjnius`) sebelum FASE 5 / rilis publik. Jangan pernah hardcode API Key di source code!
*   **Free-Tier AI Fallback — MULTI-PROVIDER (keputusan final):** User ga wajib punya API key berbayar. Semua provider di bawah gratis, dan aplikasi otomatis nge-prompt user buat isi API key pas pertama kali fitur AI dipakai, bukan wajib setup di depan — UX ini udah diimplementasi di starter code.
    *   **OpenRouter** — prioritas utama buat coding: model `qwen/qwen3-coder:free` (state-of-the-art buat code generation, context gede) dan `deepseek/deepseek-r1:free` (kuat buat reasoning-heavy debugging). Satu API key, 28+ model gratis, ga perlu kartu kredit di tier awal. **Provider ini yang udah diimplementasi penuh di `main.py` sebagai referensi.**
    *   **Groq** — buat respons instan (LPU, ratusan token/detik) kalau butuh saran cepet pas lagi ngetik, model Llama/Qwen/GPT-OSS. *(belum diimplementasi — tinggal contek pola `_call_openrouter()`)*
    *   **Mistral (La Plateforme, tier gratis)** — punya **Codestral**, model yang emang dikhususkan buat code generation & refactoring. *(belum diimplementasi)*
    *   **Gemini** — tetep dipertahankan: context window paling gede (1M token), enak buat baca banyak file sekaligus. *(belum diimplementasi)*
    *   Bungkus semua di belakang satu pola `PROVIDER_HANDLERS` (Python dict, gantiin konsep `AIProvider` interface Dart lama) biar aplikasi ga mati total kalau satu provider tiba-tiba motong kuota gratisnya.
*   **Zero Telemetry:** 100% bebas dari SDK tracker kapitalis (Firebase, Facebook SDK, dll). Privasi user adalah harga mati.

---

## 📋 FASE 1: PREPARE & ASSETS GATHERING
*Mengumpulkan bahan baku sebelum masuk ke ranah coding.*

### 1. Python Engine Package — DIGANTI TOTAL
~~Unduh pre-compiled Python binary khusus ARMv7 dari Termux, zip jadi `python_core.zip`.~~ **Ga relevan lagi.** p4a/buildozer cross-compile Python-nya sendiri, khusus buat package `com.zaba.zabacode`, otomatis sebagai bagian dari proses build. Yang perlu disiapin cuma daftar dependency di `buildozer.spec` (`requirements = python3,flask,...`) — udah ada starter-nya.

### 2. Frontend Editor Assets
*   Untuk Milestone 1: cukup `<textarea>` polos (udah ada di `templates/index.html`).
*   Untuk Milestone 3: upgrade jadi **Monaco Editor** atau **Ace Editor** — taruh build minified-nya di folder `static/`, editor-nya nanti nge-replace textarea di halaman yang SAMA (bukan integrasi terpisah kayak rencana Flutter-WebView dulu, karena seluruh app ini emang udah satu halaman web dari awal).

### 3. Database Manifest — REFRAME jadi DUA TINGKAT
Di bawah p4a, pertanyaannya bukan lagi "apa PyPI punya wheel armv7l" (itu relevan buat arsitektur Termux-bootstrap yang udah ditinggalin), tapi:
1. **`runtime`** — pure Python, ga butuh compile, aman di-install user kapan aja lewat Library Manager di app yang udah jadi.
2. **`buildtime`** — butuh C-extension, WAJIB masuk `requirements` di `buildozer.spec` dan di-rebuild lewat GitHub Actions. Ga bisa live-install di app yang udah ke-build — ini keterbatasan asli arsitektur p4a, bukan sesuatu yang gampang di-workaround.

Starter manifest (`KNOWN_LIBRARIES` di `main.py`) baru punya 3 entry (`requests`, `beautifulsoup4` = runtime; `numpy` = buildtime, karena p4a emang udah punya recipe resmi buat numpy — terverifikasi). Buat nambahin library lain ke tier `buildtime`, cek dulu apa ada recipe-nya di `https://github.com/kivy/python-for-android/tree/master/pythonforandroid/recipes` — itu sumber kebenaran yang baru, BUKAN lagi manifest ARMv7-wheel versi lama (riset PyPI-wheel sebelumnya soal `torch`/`tensorflow`/`opencv-python`/`scikit-learn`/`cryptography`/`onnxruntime`/`tflite_runtime` masih berguna sebagai konteks umum, tapi status "supported" di p4a perlu dicek ulang lewat daftar recipe, bukan diasumsikan sama).

---

## 🎯 FASE 2: FOCUS POINT & CHOOSE YOUR WEAPON

*Fokus pertama: Menghidupkan mesin belakang.*

* **Core Technology:** **python-for-android (p4a) / buildozer**, bootstrap `webview`. Seluruh UI app = satu WebView yang nampilin halaman lokal, di-serve oleh Flask yang jalan di thread Python background. Monaco/Ace Editor (Milestone 3) dan chat AI (Milestone 4) semua hidup di HALAMAN WEB YANG SAMA — bukan widget-widget Flutter terpisah.
* **Histori keputusan:** Rencana awal (Flutter + `Process.start()` ke binary Termux hasil extract) ditinggalin setelah riset nunjukin dua masalah fundamental: (1) binary Termux di-compile hardcode buat prefix `com.termux`, ga portable ke package lain tanpa rebuild total dari `termux-packages`; (2) bahkan kalau binary utamanya bisa dieksekusi (via trik rename ke `lib*.so`), C-extension `.so` yang di-`dlopen()` Python saat runtime (buat `ssl`, `sqlite3`, `numpy`, dst) tetap kena kebijakan W^X Android 10+ kalau diekstrak ke storage biasa. p4a nyelesein KEDUANYA sekaligus lewat cross-compile resmi + bootstrap `webview` yang udah teruji dipakai proyek lain (termasuk dipakai buat kombinasi Flask+WebView persis kayak yang Zabacode butuhin).

---

## 🛠️ FASE 3: STEP-BY-STEP EXECUTION

*Eksekusi bertahap secara linier dan terarah.*

### 🟩 Milestone 1: The Extraction & Hello World (Backend Core) — STARTER CODE UDAH ADA ✅

* [x] `buildozer.spec` — config packaging, target `armeabi-v7a`, bootstrap `webview`.
* [x] `main.py` — Flask backend, route `/api/run` yang eksekusi kode user (pakai `exec()` + `contextlib.redirect_stdout/stderr`, capture output/error).
* [x] `templates/index.html` — UI: textarea kode, tombol Run/Clear, output console dengan styling beda buat stdout (mint) vs stderr (merah, ala Pydroid), line:col counter di top bar.
* [ ] **BELUM dites di HP asli** — kode ini ditulis dari riset dokumentasi p4a/buildozer, bukan hasil compile beneran (sandbox yang nulis kode ini ga ada akses internet buat jalanin toolchain Android). Build pertama via GitHub Actions kemungkinan butuh 1-2 iterasi kecil nyesuain versi paket.
* [ ] **Keterbatasan yang udah dicatat, bukan dihide:** `exec()` jalan di process yang sama dengan Flask server — infinite loop / crash berat di kode user bisa nge-hang app. Isolasi ke subprocess terpisah adalah kandidat perbaikan Milestone berikutnya.

### 🟩 Milestone 2: The Shell & Pip Wrapper (Sistem Otomasi) — STARTER CODE UDAH ADA (parsial)

* [x] `zabapip` versi dua-tingkat: endpoint `/api/libraries` (list) dan `/api/libraries/install` di `main.py`, ditampilin di sidebar Library Manager.
* [x] Tier `runtime` (pure Python): coba live-install ke folder lokal via `pip install --target`, ditambahin ke `sys.path`. **BELUM PERNAH DITES** di lingkungan p4a beneran — valid secara teori, wajib divalidasi.
* [x] Tier `buildtime` (butuh C-extension): app kasih pesan jelas kalau butuh masuk `buildozer.spec` + rebuild CI, BUKAN nyoba install lalu gagal diam-diam.
* [ ] Lengkapi `KNOWN_LIBRARIES` di `main.py` seiring waktu, berdasar cek recipe p4a (lihat FASE 1 poin 3).

### 🟩 Milestone 3: The Beautiful Face (UI ala Acode & Sidebar) — SEBAGIAN sudah ada, sebagian belum

* [x] Sidebar kiri (off-canvas, slide-out) dengan 3 seksi: Library Manager, AI Assistant (status per-provider), Marketplace (placeholder, belum diimplementasi).
* [x] Line:col counter di top bar, ala Pydroid.
* [ ] Ganti `<textarea>` polos jadi Monaco/Ace Editor beneran (syntax highlighting, auto-indent) — upgrade di halaman yang sama, bukan komponen baru.
* [ ] Save/Open file `.py` ke local file system.
* [ ] Marketplace tema `.css` & plugin — masih placeholder kosong di sidebar.

### 🟩 Milestone 4: The Tsundere AI Integration (Otak Aplikasi) — STARTER CODE UDAH ADA (1 provider penuh)

* [x] UI Chat bottom-sheet (`#ai-panel`) dengan pemilihan provider.
* [x] System Instruction tsundere yang sama kayak rencana awal, ketanam di `_call_openrouter()`.
* [x] Context-Sharing beneran: karena editor & chat sekarang satu halaman web yang sama, kode yang lagi kebuka otomatis ikut terkirim tiap chat (`code: editor.value` di JS) — ga ada lagi masalah copy-paste manual.
* [x] **UX API Key auto-prompt** — kalau backend balikin `needs_key: true`, dialog inline muncul saat itu juga, minta key provider yang bersangkutan, simpan otomatis abis diisi sekali.
* [ ] Implementasi Gemini, Groq, Mistral — tinggal bikin fungsi `_call_<provider>()` ngikutin pola `_call_openrouter()` di `main.py`, terus daftarin ke `PROVIDER_HANDLERS`.
* *Opsional ke depannya:* pola `PROVIDER_HANDLERS` ini juga yang bakal dipakai kalau suatu saat mau nyambungin ke model/chatbot buatan sendiri sebagai provider tambahan yang jalan 100% lokal tanpa API key sama sekali.

---

## 🔍 FASE 4: CHECKING THE ENTIRE BUILDING (Quality Assurance)

*Pengujian menyeluruh sebelum aplikasi digunakan harian.*

* **Stress-Test RAM:** Jalankan script Python dengan loop besar, pantau penggunaan memori. Pastikan tidak terjadi *memory leak* pada WebView.
* **Sandbox Check:** Uji coba script Python nakal yang mencoba mengakses folder root sistem Android. Pastikan sandbox Android berhasil memblokirnya.
* **100% Offline Test:** Matikan paket data/Wi-Fi. Cek apakah eksekusi kode lokal (`/api/run`) tetap jalan lancar. (AI Assistant boleh tidak aktif saat offline karena butuh API eksternal — Library Manager tier `runtime` idealnya tetap jalan offline kalau pip cache-nya ada).

---

## 🚀 FASE 5: THE ANTI-CAPITALIST LEGACY

*Tahap akhir untuk membagikan karya ke dunia luar secara gratis.*

* **Secrets Cleaning:** Hapus semua API Key pribadi. `.zabacode_keys.json` (starter code) WAJIB diganti ke penyimpanan terenkripsi asli sebelum ini — lihat TODO KEAMANAN di FASE 0.
* **Production Build:** `buildozer android release` (ganti dari `flutter build apk` versi lama) untuk menghasilkan APK ARMv7 yang teroptimasi.
    > 💡 **Catatan penting (masih berlaku, toolnya aja yang beda):** buildozer/p4a + Android SDK/NDK itu berat, ga didesain jalan sebagai dev host di HP ARMv7 32-bit sendiri. Solusi: **GitHub Actions** (`.github/workflows/build_apk.yml` — udah ada starter-nya, pakai pola resmi dari repo `kivy/buildozer`) yang otomatis `buildozer android debug` di server Ubuntu GitHub tiap push — gratis buat repo publik, hasil `.apk` langsung keupload sebagai artifact / bisa dilanjut ke GitHub Release. Kode tetep ditulis dari HP, tinggal `git push`, build berat kejadian di cloud.
* **Open-Source Distribution:** Upload source code ke GitHub, sediakan `.apk` di GitHub Releases, daftarkan ke **F-Droid**.

> ⚠️ **Risiko F-Droid (masih berlaku):** F-Droid pada dasarnya ngelarang nge-bundle binary precompiled yang gak dibangun ulang oleh build server mereka sendiri. **Kabar baiknya:** karena sekarang Python di-cross-compile dari source sama p4a (bukan lagi zip binary Termux mentah), ini justru JAUH lebih align sama kebijakan F-Droid dibanding rencana awal — tapi tetap perlu dicek langsung ke dokumentasi F-Droid pas udah deket submit, karena p4a/buildozer sendiri juga narik banyak dependency build (NDK, dst) yang perlu dipastiin cara build-nya reproducible dari sudut pandang F-Droid.
