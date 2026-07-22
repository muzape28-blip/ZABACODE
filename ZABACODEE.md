# ZABACODE Roadmap & Progress Tracker

**Versi Sekarang:** `v1.0.0` (Kivy Native Edition)  
**Lisensi:** GPL v3  
**Pengembang Utama:** Zaqi (`muzape28-blip`) & Contributors

---

## 🟩 Progress Log & Changes

### 🩹 Hotfix — WebView UI Restoration & Interactive Terminal Frontend
* [x] **Restored `templates/index.html`:** File was accidentally emptied (0 bytes) in PR #4, leaving the WebView shell with a blank UI. Restored from the last good revision.
* [x] **Interactive Terminal wired to frontend:** RUN now uses `/api/run/interactive/start|output|input|stop` — real-time char streaming, live STDIN input via Enter, and the EXECUTE button doubles as STOP while a process runs.
* [x] **Removed stale `zabacode_crash.log`** from the repo and gitignored it.
* [x] **Fixed `.gitignore`:** removed the obsolete `templates/` ignore rule (WebView shell is the active UI again) that caused the template loss to go unnoticed.


### 🔥 v1.0.0 — Kivy Native Edition (MAJOR RELEASE)
* [x] **Full WebView → Kivy Migration:** Replaced Flask+WebView with native Kivy (SDL2) UI. No more local HTTP server.
* [x] **Direct Python Function Calls:** All backend operations are now direct Python calls instead of HTTP API routes. Faster and more secure.
* [x] **Pygments Syntax Highlighting:** CodeInput widget with PythonLexer for professional syntax highlighting.
* [x] **50+ Library Catalog with Offline/Online/Hybrid Tags:** Every library now has a `mode` indicator showing whether it works offline, needs internet, or is hybrid.
* [x] **6 AI Providers:** Added DeepSeek and Ollama (offline!) alongside OpenRouter, Gemini, Groq, and Mistral.
* [x] **10 Themes:** Added Tokyo Night, One Dark, Gruvbox Dark, and Catppuccin Mocha.
* [x] **6-Language i18n:** Full translations for Indonesian, English, Japanese, Korean, Arabic, and Spanish.
* [x] **12 Plugins + 8 Snippets:** Added Code Minifier, JSON Formatter, Regex Tester, Color Picker, Markdown Preview, Code Timer, ASCII Art, and TODO Manager.
* [x] **Background Threading:** AI calls and library installations run in background threads to keep UI responsive.
* [x] **Security hardening:** Removed the exposed HTTP server; package downloads verify TLS; wheel paths are validated; Android Keystore is preferred for API keys with an in-memory-only fallback.
* [x] **Responsive Design:** Kivy's native layout system with dp/sp sizing ensures proper scaling on all screen sizes.
* [x] **78 Unit Tests:** Comprehensive test suite covering execution, checker, file manager, security, library manager, themes, i18n, plugins, and AI providers.

### 🟩 v0.3.5 (Pre-Kivy, WebView Edition)
* [x] Local Session Auth Token Security (`X-Zabacode-Token`)
* [x] Real Android Keystore Integration
* [x] Addon Plugin & Theme Marketplace
* [x] PyPI direct extractor (TLS verification required)
* [x] Fix Monaco Mobile Soft Keyboard Focus
* [x] XSS HTML Sanitization
* [x] Dependency Completion
