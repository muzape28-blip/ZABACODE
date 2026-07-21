<p align="center">
  <img src="assets/logo.png" alt="ZABACODE Logo" width="220" height="220">
</p>

<h1 align="center">⚡ ZABACODE (Panduan Bahasa Indonesia) ⚡</h1>

<p align="center">
  <b>Mobile Python IDE Standalone Anti-Kapitalis & AI Code Assistant untuk Android</b>
</p>

<p align="center">
  <i>Menggabungkan kekuatan eksekusi murni <b>Pydroid 3</b> dengan kerapihan UI, multi-tab, & kontrol <b>Acode</b> — 100% Gratis, Open Source, & Zero Telemetry.</i>
</p>

<p align="center">
  <a href="README.md"><b>🌐 Switch to English Documentation</b></a>
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
│  ZABACODE — Mobile Engine Active                                            │
│  [ OK ] Subprocess Sandbox Engine Ready                                     │
│  [ OK ] Local Session Auth Token Security Active (X-Zabacode-Token)         │
│  [ OK ] Android Keystore Encrypted Key Storage Active                       │
│  [ OK ] Path Resolver Active (_active_run.py -> Path(__file__) OK)          │
│  [ OK ] Direct PyPI Wheel Extractor Active (SSL & SIGSEGV -11 Bypass)       │
│  [ OK ] Dual Engine Core: Monaco (Deterministic LineHeight) + Native Engine │
│  [ OK ] Bilingual Support Engine Active (Indonesian & English i18n)         │
│  > WORKSPACE READY. SELAMAT NGODING!_                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏛️ Lore & Filosofi Malaikat Zabaniyah

Nama **ZABACODE** terinspirasi dari ketangguhan dan ketegasan **Malaikat Zabaniyah** — entitas penjaga legendaris yang tangguh dan tidak kenal kompromi. 

Di tengah ekosistem aplikasi mobile yang dipenuhi oleh iklan mengganggu, *paywall* agresif, penambangan data pribadi (*telemetry*), dan biaya langganan, **ZABACODE berdiri sebagai simbol perlawanan anti-kapitalis**:
* **100% Gratis & Open-Source (GPLv3)**
* **Bebas Iklan Banner / Pop-up**
* **Zero Telemetry / Zero Tracking**
* **Eksekusi Lokal Terisolasi (Offline First)**

---

## ✨ Fitur-Fitur Utama

### 🧠 1. Subprocess Isolation & Auto `__file__` Resolution
* Eksekusi kode terisolasi dalam *subprocess* dengan batas timeout 30s.
* Penulisan skrip temporary `_active_run.py` menjamin `Path(__file__)` terdefinisi sempurna tanpa `NameError`.

### 📦 2. Library Manager (`zabapip`) & Direct PyPI Extractor
* Ekstraksi paket Wheel `.whl` langsung via PyPI API dengan **SSL Bypass Context** (`ssl.CERT_NONE`), kebal dari crash `SIGSEGV (-11)` di Android.
* Pilihan instalasi pustaka kustom dari PyPI secara langsung.

### ⚙️ 3. Fix Monaco Cursor & Multi-Language UI (i18n)
* **Deterministic LineHeight:** Kursor koding Monaco berjalan presisi mengikuti baris aktif di Android WebView.
* **1-Click Language Switcher:** Berpindah seketika antara Bahasa Indonesia dan Bahasa Inggris via sidebar.
* **Simplifikasi Header Topbar:** Menampilkan judul bersih `ZABACODE`.

### 🧩 4. Addon Plugin & Theme Marketplace Functionality
* Marketplace lengkap dengan plugin fungsional: **Auto-Code Formatter (PEP-8)**, **Python Snippets Pack**, **Syntax Linter Guard**, dan **Extended Mobile Symbol Bar** (tombol simbol cepat di atas keyboard).

---

## 👥 Tim & Kontributor

* **[Zaqi (`muzape28-blip`)](https://github.com/muzape28-blip)** — *Creator, Lead Developer & Architect*
* **[Arena.ai Agent](https://arena.ai)** — *AI Co-Developer & Code Engineer*
