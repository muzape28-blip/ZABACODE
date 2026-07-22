<p align="center">
  <img src="assets/logo.png" alt="ZABACODE Logo" width="220" height="220">
</p>

<h1 align="center">⚡ ZABACODE (Panduan Bahasa Indonesia) ⚡</h1>

<p align="center">
  <b>Mobile Python IDE Standalone Anti-Kapitalis & AI Code Assistant untuk Android</b>
</p>

<p align="center">
  <i>Menggabungkan kekuatan eksekusi murni <b>Pydroid 3</b> dengan kerapihan UI, multi-tab, & kontrol <b>Acode</b> — kini memakai <b>WebView shell di atas core Python modular</b> — 100% Gratis, Open Source, & Zero Telemetry.</i>
</p>

<p align="center">
  <a href="README.md"><b>🌐 Switch to English Documentation</b></a>
</p>

<p align="center">
  <a href="https://github.com/muzape28-blip/ZABACODE/actions/workflows/build_apk.yml"><img src="https://github.com/muzape28-blip/ZABACODE/actions/workflows/build_apk.yml/badge.svg" alt="Build Status"></a>
  <a href="https://github.com/muzape28-blip/ZABACODE/releases"><img src="https://img.shields.io/badge/Release-v1.0.0-39FF14.svg?style=flat&logo=android" alt="Version"></a>
  <a href="https://www.gnu.org/licenses/gpl-3.0"><img src="https://img.shields.io/badge/License-GPLv3-blue.svg" alt="GPLv3 License"></a>
  <img src="https://img.shields.io/badge/Architecture-ARMv7%20%7C%20ARM64-FFB000.svg" alt="Architecture">
  <img src="https://img.shields.io/badge/UI-WebView%20Shell-147885.svg" alt="WebView Shell">
  <img src="https://img.shields.io/badge/Telemetry-ZERO-brightgreen.svg" alt="Zero Telemetry">
  <img src="https://img.shields.io/badge/Privacy-100%25%20Offline%20First-success.svg" alt="Offline First">
</p>

---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ZABACODE v1.0.0 — WebView Shell + Core Python Modular                    │
│  [ OK ] Local WebView UI Engine Active                                     │
│  [ OK ] Core Engine Modular Active                                         │
│  [ OK ] Subprocess Runner dengan Timeout & Process-Group Cleanup           │
│  [ OK ] Android Keystore untuk API Key Aktif                                │
│  [ OK ] Direct PyPI Wheel Extractor dengan Verifikasi TLS                  │
│  [ OK ] Multi-Provider AI Engine (6 Provider: OpenRouter/Gemini/Groq/     │
│         Mistral/DeepSeek/Ollama)                                           │
│  [ OK ] Multi-Language i18n Engine (6 Bahasa: ID/EN/JA/KO/AR/ES)         │
│  [ OK ] Theme Engine Active (10 Tema incl. Tokyo Night/Catppuccin)       │
│  [ OK ] Plugin Marketplace Active (12 Plugin, 8 Snippet)                 │
│  [ OK ] Library Manager (50+ Pustaka dengan Tag Offline/Online)          │
│  > WORKSPACE READY. SELAMAT NGODING!_                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏛️ Lore & Filosofi Malaikat Zabaniyah

Nama **ZABACODE** terinspirasi dari ketangguhan dan ketegasan **Malaikat Zabaniyah** — entitas penjaga legendaris yang tangguh dan tidak kenal kompromi. 

Di tengah ekosistem aplikasi mobile yang dipenuhi oleh iklan mengganggu, *paywall* agresif, penambangan data pribadi (*telemetry*), dan biaya langganan, **ZABACODE berdiri sebagai simbol perlawanan anti-kapitalis**:
* **100% Gratis & Open-Source (GPLv3)**
* **Bebas Iklan Banner / Pop-up**
* **Zero Telemetry / Zero Tracking**
* **Eksekusi kode local-first (inti offline)**

---

## 🆕 Apa yang Baru di v1.0.0 (Kivy Native Edition)

### 🔥 Besar: Core modular + WebView shell kompatibel
UI memakai WebView lokal, sedangkan core v1.0.0 tetap modular untuk eksekusi, file, package, tema, plugin, dan AI. Perubahan ini menghindari jalur startup Kivy yang force close pada ARMv7 tanpa membuang perbaikan core.
- **UI compatibility-first** — kembali ke WebView yang lebih stabil untuk perangkat ini
- **Core modular tetap dipakai** — modul executor, security, file, package, dan provider tetap terpisah
- **Server hanya localhost** — shell hanya bind ke `127.0.0.1`
- **Inti tetap offline-first** — edit dan eksekusi lokal tidak butuh internet

### 📦 2. Library Manager Diperkaya — 50+ Pustaka dengan Tag Offline/Online
Setiap pustaka kini memiliki tag `mode`:
- 🟢 **offline** — Berfungsi 100% tanpa internet
- 🔵 **online** — Memerlukan internet
- 🟡 **hybrid** — Fitur utama offline, beberapa fitur perlu internet

### 🤖 3. Multi-Provider AI — 6 Provider
* OpenRouter, Gemini, Groq, Mistral, **DeepSeek** *(BARU)*, **Ollama (Offline!)** *(BARU)*

### 🎨 4. 10 Tema
* Retro Green, Solarized Dark, Dracula, Cyberpunk Neon, Nord Arctic, Monokai Pro
* **Tokyo Night** *(BARU)*, **One Dark** *(BARU)*, **Gruvbox Dark** *(BARU)*, **Catppuccin Mocha** *(BARU)*

### 🌐 5. Multi-Bahasa — 6 Bahasa
🇮🇩 Indonesia, 🇬🇧 English, 🇯🇵 日本語, 🇰🇷 한국어, 🇸🇦 العربية, 🇪🇸 Español

### 🧩 6. Plugin Marketplace — 12 Plugin + 8 Snippet
Plugin baru: Code Minifier, JSON Formatter, Regex Tester, Color Picker, Markdown Preview, Code Timer, ASCII Art, TODO Manager

---

## 👥 Tim & Kontributor

* **[Zaqi (`muzape28-blip`)](https://github.com/muzape28-blip)** — *Creator, Lead Developer & Architect*
* **[Arena.ai Agent](https://arena.ai)** — *AI Co-Developer & Code Engineer*
* **Elicit AI** — *Security hardening, code review & release-quality engineering*
