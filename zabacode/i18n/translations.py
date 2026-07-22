"""
ZABACODE i18n — Multi-Language Translation Engine
Supports: Indonesian (id), English (en), Japanese (ja), Korean (ko), Arabic (ar), Spanish (es)
"""

from zabacode.core.paths import APP_DIR

# Default language
DEFAULT_LANG = "id"  # Indonesian as default

# Translation dictionary
TRANSLATIONS = {
    # ---- Indonesian (id) ----
    "id": {
        # App
        "app_title": "ZABACODE",
        "app_subtitle": "Mobile Python IDE & AI Assistant",
        "version": "Versi",
        
        # Top bar
        "status_ready": "Siap",
        "status_running": "Menjalankan...",
        "status_error": "Error",
        "status_ok": "Selesai",
        "line_col": "Br {line}, Kl {col}",
        
        # Tabs
        "new_tab": "Baru",
        "untitled": "tanpa_judul",
        
        # Actions
        "run": "▶ JALANKAN",
        "stop": "⏹ BERHENTI",
        "clear": "BERSIHKAN",
        "check": "CEK KODE",
        
        # Sidebar
        "sidebar_title": "ZABACODE",
        "files": "📁 Berkas",
        "save": "💾 Simpan",
        "libraries": "📦 Pustaka",
        "ai_keys": "🔑 Kunci AI",
        "themes": "🎨 Tema",
        "plugins": "🧩 Plugin",
        "language": "🌐 Bahasa",
        "settings": "⚙️ Pengaturan",
        "about": "ℹ️ Tentang",
        "output": "📤 Output",
        
        # File Manager
        "file_manager": "Manajer Berkas",
        "file_name": "Nama File",
        "file_open": "Buka",
        "file_save": "Simpan",
        "file_delete": "Hapus",
        "file_new": "Buat Baru",
        "file_empty": "Belum ada file tersimpan.",
        "file_saved": "File disimpan!",
        "file_deleted": "File dihapus!",
        "file_not_found": "File tidak ditemukan.",
        "file_invalid_name": "Nama file tidak valid.",
        "file_too_large": "Isi file terlalu besar.",
        "confirm_delete": "Hapus file {name}?",
        
        # Library Manager
        "lib_manager": "Manajer Pustaka",
        "lib_install": "Install",
        "lib_installed": "Terinstall",
        "lib_installing": "Menginstall...",
        "lib_install_success": "Berhasil diinstall!",
        "lib_install_fail": "Gagal menginstall.",
        "lib_needs_rebuild": "Perlu rebuild APK",
        "lib_mode_offline": "Offline",
        "lib_mode_online": "Online",
        "lib_mode_hybrid": "Hybrid",
        "lib_category_all": "Semua",
        
        # AI Panel
        "ai_title": "🤖 Zaba AI",
        "ai_provider": "Provider",
        "ai_input_placeholder": "Tanya sesuatu...",
        "ai_send": "Kirim",
        "ai_needs_key": "API Key {provider} belum diset. Silakan masukkan di menu Kunci AI.",
        "ai_error": "AI Error: {error}",
        
        # AI Keys
        "ai_keys_title": "Kunci API AI",
        "ai_key_provider": "Provider",
        "ai_key_input_placeholder": "Masukkan API key...",
        "ai_key_save": "Simpan",
        "ai_key_saved": "Kunci API {provider} disimpan secara terenkripsi.",
        "ai_key_delete": "Hapus",
        "ai_key_status_active": "Aktif",
        "ai_key_status_empty": "Belum diset",
        
        # Themes
        "theme_title": "Pilih Tema",
        "theme_applied": "Tema diterapkan!",
        
        # Plugins
        "plugin_title": "Plugin & Addon",
        "plugin_install": "Aktifkan",
        "plugin_installed": "Aktif",
        "plugin_description": "Deskripsi",
        
        # Language
        "lang_title": "Pilih Bahasa",
        "lang_applied": "Bahasa diubah!",
        
        # About
        "about_title": "Tentang ZABACODE",
        "about_version": "Versi {version}",
        "about_license": "Lisensi: GPLv3",
        "about_author": "Pengembang: Zaqi (muzape28-blip)",
        "about_philosophy": "Anti-Kapitalist Mobile Python IDE\n100% Gratis, Open Source, Zero Telemetry",
        "about_close": "Tutup",
        
        # Code Checker
        "check_valid": "✅ Kode valid! Siap dijalankan.",
        "check_invalid": "⚠️ Ditemukan masalah:",
        "check_hint": "Perbaiki semua masalah sebelum menjalankan.",
        
        # Output
        "output_stdout": "Output",
        "output_stderr": "Error",
        "output_timeout": "Proses timeout setelah {timeout}s",
        "output_truncated": "[Output dipotong]",
        
        # Common
        "cancel": "Batal",
        "close": "Tutup",
        "ok": "OK",
        "yes": "Ya",
        "no": "Tidak",
        "loading": "Memuat...",
        "error": "Error",
        "success": "Berhasil",
        "warning": "Peringatan",
    },
    
    # ---- English (en) ----
    "en": {
        "app_title": "ZABACODE",
        "app_subtitle": "Mobile Python IDE & AI Assistant",
        "version": "Version",
        
        "status_ready": "Ready",
        "status_running": "Running...",
        "status_error": "Error",
        "status_ok": "Done",
        "line_col": "Ln {line}, Col {col}",
        
        "new_tab": "New",
        "untitled": "untitled",
        
        "run": "▶ RUN",
        "stop": "⏹ STOP",
        "clear": "CLEAR",
        "check": "CHECK CODE",
        
        "sidebar_title": "ZABACODE",
        "files": "📁 Files",
        "save": "💾 Save",
        "libraries": "📦 Libraries",
        "ai_keys": "🔑 AI Keys",
        "themes": "🎨 Themes",
        "plugins": "🧩 Plugins",
        "language": "🌐 Language",
        "settings": "⚙️ Settings",
        "about": "ℹ️ About",
        "output": "📤 Output",
        
        "file_manager": "File Manager",
        "file_name": "Filename",
        "file_open": "Open",
        "file_save": "Save",
        "file_delete": "Delete",
        "file_new": "New File",
        "file_empty": "No saved files yet.",
        "file_saved": "File saved!",
        "file_deleted": "File deleted!",
        "file_not_found": "File not found.",
        "file_invalid_name": "Invalid filename.",
        "file_too_large": "File content too large.",
        "confirm_delete": "Delete file {name}?",
        
        "lib_manager": "Library Manager",
        "lib_install": "Install",
        "lib_installed": "Installed",
        "lib_installing": "Installing...",
        "lib_install_success": "Successfully installed!",
        "lib_install_fail": "Installation failed.",
        "lib_needs_rebuild": "Needs APK rebuild",
        "lib_mode_offline": "Offline",
        "lib_mode_online": "Online",
        "lib_mode_hybrid": "Hybrid",
        "lib_category_all": "All",
        
        "ai_title": "🤖 Zaba AI",
        "ai_provider": "Provider",
        "ai_input_placeholder": "Ask something...",
        "ai_send": "Send",
        "ai_needs_key": "API Key for {provider} not set. Please enter it in AI Keys menu.",
        "ai_error": "AI Error: {error}",
        
        "ai_keys_title": "AI API Keys",
        "ai_key_provider": "Provider",
        "ai_key_input_placeholder": "Enter API key...",
        "ai_key_save": "Save",
        "ai_key_saved": "API key for {provider} saved encrypted.",
        "ai_key_delete": "Delete",
        "ai_key_status_active": "Active",
        "ai_key_status_empty": "Not set",
        
        "theme_title": "Choose Theme",
        "theme_applied": "Theme applied!",
        
        "plugin_title": "Plugins & Addons",
        "plugin_install": "Enable",
        "plugin_installed": "Active",
        "plugin_description": "Description",
        
        "lang_title": "Choose Language",
        "lang_applied": "Language changed!",
        
        "about_title": "About ZABACODE",
        "about_version": "Version {version}",
        "about_license": "License: GPLv3",
        "about_author": "Developer: Zaqi (muzape28-blip)",
        "about_philosophy": "Anti-Capitalist Mobile Python IDE\n100% Free, Open Source, Zero Telemetry",
        "about_close": "Close",
        
        "check_valid": "✅ Code is valid! Ready to run.",
        "check_invalid": "⚠️ Issues found:",
        "check_hint": "Fix all issues before running.",
        
        "output_stdout": "Output",
        "output_stderr": "Error",
        "output_timeout": "Process timed out after {timeout}s",
        "output_truncated": "[Output truncated]",
        
        "cancel": "Cancel",
        "close": "Close",
        "ok": "OK",
        "yes": "Yes",
        "no": "No",
        "loading": "Loading...",
        "error": "Error",
        "success": "Success",
        "warning": "Warning",
    },
}

# Supported languages display names
LANGUAGES = {
    "id": "🇮🇩 Bahasa Indonesia",
    "en": "🇬🇧 English",
}


class I18n:
    """Internationalization engine with fallback support."""
    
    def __init__(self, lang: str = DEFAULT_LANG):
        self.lang = lang
    
    def t(self, key: str, **kwargs) -> str:
        """
        Translate a key to the current language.
        Supports format string kwargs: t("line_col", line=1, col=5)
        Falls back to English, then to key itself.
        """
        # Try current language
        text = TRANSLATIONS.get(self.lang, {}).get(key)
        if text is None:
            # Fallback to English
            text = TRANSLATIONS.get("en", {}).get(key)
        if text is None:
            # Fallback to key
            return key
        
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, IndexError):
                return text
        return text
    
    def set_language(self, lang: str) -> None:
        """Set the current language."""
        if lang in TRANSLATIONS:
            self.lang = lang
    
    def get_language(self) -> str:
        """Get the current language code."""
        return self.lang
    
    def get_available_languages(self) -> dict:
        """Get all available languages."""
        return LANGUAGES.copy()


# Global i18n instance
i18n = I18n()
