<p align="center">
  <img src="assets/logo.png" alt="ZABACODE Logo" width="220" height="220">
</p>

<h1 align="center">⚡ ZABACODE ⚡</h1>

<p align="center">
  <b>Standalone Anti-Capitalist Mobile Python IDE & AI Code Assistant for Android</b>
</p>

<p align="center">
  <i>Combining the raw execution power of <b>Pydroid 3</b> with the detail, multi-tab elegance & UI mastery of <b>Acode</b> — 100% Free, Open Source, & Zero Telemetry.</i>
</p>

<p align="center">
  <a href="https://github.com/muzape28-blip/ZABACODE/actions/workflows/build_apk.yml"><img src="https://github.com/muzape28-blip/ZABACODE/actions/workflows/build_apk.yml/badge.svg" alt="Build Status"></a>
  <a href="https://github.com/muzape28-blip/ZABACODE/releases"><img src="https://img.shields.io/badge/Release-v0.3.5-39FF14.svg?style=flat&logo=android" alt="Version"></a>
  <a href="https://www.gnu.org/licenses/gpl-3.0"><img src="https://img.shields.io/badge/License-GPLv3-blue.svg" alt="GPLv3 License"></a>
  <img src="https://img.shields.io/badge/Architecture-ARMv7%20%7C%20ARM64-FFB000.svg" alt="Architecture">
  <img src="https://img.shields.io/badge/Telemetry-ZERO-brightgreen.svg" alt="Zero Telemetry">
  <img src="https://img.shields.io/badge/Privacy-100%25%20Offline%20First-success.svg" alt="Offline First">
</p>

---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ZABACODE v0.3.5 — Standalone Mobile Engine Active                          │
│  [ OK ] Subprocess Sandbox Engine Ready                                     │
│  [ OK ] Path Resolver Active (_active_run.py -> Path(__file__) OK)          │
│  [ OK ] Direct PyPI Wheel Extractor Active (SIGSEGV -11 Bypass)             │
│  [ OK ] Dual Engine Core: Monaco (Auto-Wrap) + Native Light Engine          │
│  [ OK ] Multi-Provider AI (Qwen 2.5 Coder, Gemini 1.5, Groq, Mistral) Ready │
│  > WORKSPACE READY. HAPPY CODING!_                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏛️ Lore & Philosophy

Nama **ZABACODE** terinspirasi dari ketangguhan, ketegasan, dan kekuatan **Malaikat Zabaniyah** — entitas penjaga legendaris yang tidak kenal kompromi. 

Dalam dunia pengembangan software mobile yang dipenuhi oleh aplikasi beriklan, paywall agresif, penambangan data pribadi (*telemetry*), dan langganan bulanan mahal, **ZABACODE hadir sebagai perlawanan anti-kapitalis**:
* **100% Gratis & Open-Source (GPLv3)**
* **Tanpa Iklan Banner / Pop-up Membagongkan**
* **Zero Telemetry / Zero Data Harvesting**
* **Eksekusi Lokal Terisolasi (Offline-Capable)**

---

## ✨ Feature Highlights (`v0.3.5`)

### 🧠 1. Subprocess Isolation & Automatic `__file__` Resolution
* **Full Process Isolation:** Setiap skrip Python dieksekusi di dalam *subprocess* terpisah dengan batas *timeout* 30 detik untuk memitigasi *infinite loop* yang menyandera aplikasi.
* **Automatic `__file__` Fix:** Eksekusi kode secara otomatis menggunakan skrip sementara `_active_run.py`. Pemanggilan `Path(__file__)` atau `__file__` **berjalan 100% sempurna** tanpa pernah mengalami `NameError: name '__file__' is not defined`.

### 📦 2. Dedicated Library Manager (`zabapip`) & PyPI Direct Extractor
* **Fullscreen Dedicated Modal View:** Tampilan manajer pustaka kini disajikan penuh dalam bentuk *Card Grid* dengan pencarian real-time dan filter kategori (`Web & API`, `Data & Sains`, `AI & Database`, `Media & Utils`).
* **SIGSEGV (-11) Bypass via Direct PyPI Extractor:** Apabila eksekusi `pip` subprocess bawaan mengalami *Segmentation Fault* (-11) akibat batasan kernel Android, Zabacode secara otomatis beralih menggunakan **PyPI JSON API + `zipfile` internal** untuk mengunduh dan mengekstrak Pure Python Wheel (`.whl`) secara bersih.
* **Custom PyPI Installer:** Pengguna dapat memasukkan nama pustaka Python *apa saja* dari PyPI dan menginstalnya langsung ke direktori internal `user_packages`.

### ⚙️ 3. Dual Engine Editor Core (Monaco ↔ Native Light)
* **Adaptive Monaco Editor:** Dilengkapi dengan *Soft Auto-Wrap*, pembersihan total garis highlight putih overlay pada baris aktif, dan penomoran baris yang tetap terhitung 1 baris.
* **1-Click Engine Switcher:** Terdapat tombol **`⚙️ ENGINE: MONACO / NATIVE`** di sidebar untuk berpindah ke **Native Textarea Light Engine** kapan saja saat membutuhkan performa ekstra ringan pada HP dengan RAM terbatas.

### 🖼️ 4. Inline Terminal Plot & Image Renderer
* Eksekusi kode Python yang menghasilkan file gambar/grafik baru di folder workspace (seperti diagram `matplotlib` atau pengolahan gambar `PIL`/`Pillow`) secara otomatis dideteksi dan ditampilkan secara **inline di terminal output**.

### 🤖 5. Multi-Provider AI Assistant & 1-Click Auto-Fix
* Terintegrasi dengan 4 provider AI terkemuka tanpa perantara:
  * **OpenRouter** (`qwen/qwen-2.5-coder-32b-instruct:free`)
  * **Google Gemini** (`gemini-1.5-flash`)
  * **Groq** (`llama-3.1-8b-instant`)
  * **Mistral** (`codestral-latest`)
* **`⚡ ZABA AI: BENERIN ERROR INI!`**: Tombol auto-fix otomatis muncul di terminal ketika terjadi Traceback error untuk menganalisis dan memberikan perbaikan instan.

### 📱 6. Universal Dual-Arch Android Compatibility
* Didukung oleh kompilasi automatik `buildozer.spec` untuk arsitektur **`armeabi-v7a` (32-bit)** dan **`arm64-v8a` (64-bit)**, menjamin kelancaran baik di HP Android hemat spesifikasi (seperti Infinix Smart series) maupun HP Android flagship terbaru.

---

## 🏗️ Architecture & Data Flow

```
 ┌─────────────────────────────────────────────────────────┐
│              Android Webview Front-End UI               │
│    (Adaptive Monaco Editor / Native Engine + Multi-Tab) │
└────────────────────────────┬────────────────────────────┘
                             │ HTTP REST API (127.0.0.1:5000)
┌────────────────────────────▼────────────────────────────┐
│              Flask + Waitress Backend Server            │
│                     (main.py)                           │
└─────┬──────────────────────┬──────────────────────┬─────┘
      │                      │                      │
┌─────▼───────────────┐ ┌────▼───────────────┐ ┌────▼───────────────┐
│ Isolated Subprocess │ │ Direct PyPI Extractor│ │ Multi-Provider AI │
│ Code Execution Engine│ │  (urllib + zipfile)│ │ (OpenRouter/Gemini│
│ (_active_run.py)    │ │  (user_packages)   │ │  /Groq/Mistral)   │
└─────────────────────┘ └────────────────────┘ └───────────────────┘
```

---

## 📊 Comparison: ZABACODE vs Pydroid 3 vs Acode

| Fitur / Karakteristik | 🐍 Pydroid 3 | 📝 Acode | ⚡ ZABACODE v0.3.5 |
| :--- | :--- | :--- | :--- |
| **Model Lisensi** | Freemium / Paywall | Berbayar Play Store | **100% Gratis & Open-Source (GPLv3)** |
| **Iklan & Telemetry** | Ada Iklan & Tracker | Ada Analytics | **ZERO Telemetry & ZERO Ads** |
| **Python Execution Engine**| ✅ Native | ❌ Butuh Termux | ✅ **Isolated Subprocess Sandbox** |
| **UI Editor Engine** | ⚠️ Kaku / IDLE Style | ✅ Modern Ace/Monaco | ✅ **Adaptive Monaco + Native Light Engine** |
| **AI Assistant Built-in** | ❌ Tidak Ada | ❌ Tidak Ada | 🚀 **Multi-Provider AI + 1-Click Auto-Fix** |
| **Library Manager** | ✅ Precompiled Wheels | ❌ Tidak Ada | 🚀 **`zabapip` + PyPI Direct Wheel Extractor** |
| **Dukungan Arsitektur** | 32-bit / 64-bit | - | ✅ **Universal Fat APK (ARMv7 + ARM64)** |

---

## 🚀 Quick Start & Installation

### Option 1: Download Pre-compiled APK (Recommended)
1. Buka halaman [GitHub Releases](https://github.com/muzape28-blip/ZABACODE/releases) atau tab **Actions** pada repo ini.
2. Unduh file `Zabacode-Universal-v0.3.5.apk`.
3. Install di HP Android kamu (Android 8.0 / API 26 ke atas).

### Option 2: Running Development Server Locally

```bash
# 1. Clone repositori ini
git clone https://github.com/muzape28-blip/ZABACODE.git
cd ZABACODE

# 2. Install dev dependencies
pip install -r requirements-dev.txt

# 3. Jalankan backend Flask
python main.py

# 4. Buka browser di http://127.0.0.1:5000
```

### Option 3: Compiling APK Cloud via GitHub Actions

Cukup lakukan `push` atau `git tag` ke branch `main`, workflow `.github/workflows/build_apk.yml` akan secara otomatis mengompilasi APK siap pakai di cloud dalam hitungan menit!

---

## 👥 Core Team & Contributors

<p align="left">
  <a href="https://github.com/muzape28-blip">
    <img src="https://github.com/muzape28-blip.png" width="60" height="60" style="border-radius:50%" alt="Zaqi">
  </a>
  &nbsp;&nbsp;
  <a href="https://arena.ai">
    <img src="https://arena.ai/favicon.ico" width="60" height="60" style="border-radius:50%" alt="Arena.ai Agent">
  </a>
</p>

* **[Zaqi (`muzape28-blip`)](https://github.com/muzape28-blip)** — *Creator, Lead Developer & Architect*
* **[Arena.ai Agent](https://arena.ai)** — *AI Co-Developer & Code Engineer*

---

## 📜 License & Freedom Statement

Program ini adalah perangkat lunak bebas: Anda dapat mendistribusikannya kembali dan/atau memodifikasinya di bawah persyaratan **GNU General Public License (GPLv3)** sebagaimana dipublikasikan oleh Free Software Foundation.

```
Copyright (C) 2026 Zaqi (muzape28-blip) and ZABACODE Contributors.
ZABACODE comes with ABSOLUTELY NO WARRANTY.
```

---

<p align="center">
  <b>Built with ❤️ and 🔥 for the global open-source community.</b>
</p>
