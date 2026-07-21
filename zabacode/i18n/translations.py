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
    
    # ---- Japanese (ja) ----
    "ja": {
        "app_title": "ZABACODE",
        "app_subtitle": "モバイルPython IDE & AIアシスタント",
        "version": "バージョン",
        
        "status_ready": "準備完了",
        "status_running": "実行中...",
        "status_error": "エラー",
        "status_ok": "完了",
        "line_col": "行 {line}, 列 {col}",
        
        "new_tab": "新規",
        "untitled": "無題",
        
        "run": "▶ 実行",
        "stop": "⏹ 停止",
        "clear": "クリア",
        "check": "コードチェック",
        
        "sidebar_title": "ZABACODE",
        "files": "📁 ファイル",
        "save": "💾 保存",
        "libraries": "📦 ライブラリ",
        "ai_keys": "🔑 AIキー",
        "themes": "🎨 テーマ",
        "plugins": "🧩 プラグイン",
        "language": "🌐 言語",
        "settings": "⚙️ 設定",
        "about": "ℹ️ バージョン情報",
        "output": "📤 出力",
        
        "file_manager": "ファイルマネージャー",
        "file_name": "ファイル名",
        "file_open": "開く",
        "file_save": "保存",
        "file_delete": "削除",
        "file_new": "新規作成",
        "file_empty": "保存されたファイルはありません。",
        "file_saved": "ファイルを保存しました！",
        "file_deleted": "ファイルを削除しました！",
        "file_not_found": "ファイルが見つかりません。",
        "file_invalid_name": "無効なファイル名。",
        "file_too_large": "ファイルが大きすぎます。",
        "confirm_delete": "ファイル {name} を削除しますか？",
        
        "lib_manager": "ライブラリマネージャー",
        "lib_install": "インストール",
        "lib_installed": "インストール済み",
        "lib_installing": "インストール中...",
        "lib_install_success": "インストール成功！",
        "lib_install_fail": "インストール失敗。",
        "lib_needs_rebuild": "APKの再ビルドが必要",
        "lib_mode_offline": "オフライン",
        "lib_mode_online": "オンライン",
        "lib_mode_hybrid": "ハイブリッド",
        "lib_category_all": "すべて",
        
        "ai_title": "🤖 Zaba AI",
        "ai_provider": "プロバイダー",
        "ai_input_placeholder": "何か聞いてください...",
        "ai_send": "送信",
        "ai_needs_key": "{provider} のAPIキーが設定されていません。",
        "ai_error": "AIエラー: {error}",
        
        "ai_keys_title": "AI APIキー",
        "ai_key_provider": "プロバイダー",
        "ai_key_input_placeholder": "APIキーを入力...",
        "ai_key_save": "保存",
        "ai_key_saved": "{provider} のAPIキーを暗号化保存しました。",
        "ai_key_delete": "削除",
        "ai_key_status_active": "有効",
        "ai_key_status_empty": "未設定",
        
        "theme_title": "テーマを選択",
        "theme_applied": "テーマを適用しました！",
        
        "plugin_title": "プラグイン＆アドオン",
        "plugin_install": "有効化",
        "plugin_installed": "有効",
        "plugin_description": "説明",
        
        "lang_title": "言語を選択",
        "lang_applied": "言語を変更しました！",
        
        "about_title": "ZABACODEについて",
        "about_version": "バージョン {version}",
        "about_license": "ライセンス: GPLv3",
        "about_author": "開発者: Zaqi (muzape28-blip)",
        "about_philosophy": "アンチ資本主義モバイルPython IDE\n100%無料、オープンソース、ゼロテレメトリ",
        "about_close": "閉じる",
        
        "check_valid": "✅ コードは有効です！実行可能。",
        "check_invalid": "⚠️ 問題が見つかりました：",
        "check_hint": "実行前にすべての問題を修正してください。",
        
        "output_stdout": "出力",
        "output_stderr": "エラー",
        "output_timeout": "{timeout}秒後にタイムアウトしました",
        "output_truncated": "[出力が切り詰められました]",
        
        "cancel": "キャンセル",
        "close": "閉じる",
        "ok": "OK",
        "yes": "はい",
        "no": "いいえ",
        "loading": "読み込み中...",
        "error": "エラー",
        "success": "成功",
        "warning": "警告",
    },
    
    # ---- Korean (ko) ----
    "ko": {
        "app_title": "ZABACODE",
        "app_subtitle": "모바일 Python IDE & AI 어시스턴트",
        "version": "버전",
        
        "status_ready": "준비",
        "status_running": "실행 중...",
        "status_error": "오류",
        "status_ok": "완료",
        "line_col": "줄 {line}, 열 {col}",
        
        "new_tab": "새 탭",
        "untitled": "제목없음",
        
        "run": "▶ 실행",
        "stop": "⏹ 중지",
        "clear": "지우기",
        "check": "코드 검사",
        
        "sidebar_title": "ZABACODE",
        "files": "📁 파일",
        "save": "💾 저장",
        "libraries": "📦 라이브러리",
        "ai_keys": "🔑 AI 키",
        "themes": "🎨 테마",
        "plugins": "🧩 플러그인",
        "language": "🌐 언어",
        "settings": "⚙️ 설정",
        "about": "ℹ️ 정보",
        "output": "📤 출력",
        
        "file_manager": "파일 관리자",
        "file_name": "파일명",
        "file_open": "열기",
        "file_save": "저장",
        "file_delete": "삭제",
        "file_new": "새 파일",
        "file_empty": "저장된 파일이 없습니다.",
        "file_saved": "파일이 저장되었습니다!",
        "file_deleted": "파일이 삭제되었습니다!",
        "file_not_found": "파일을 찾을 수 없습니다.",
        "file_invalid_name": "잘못된 파일명입니다.",
        "file_too_large": "파일이 너무 큽니다.",
        "confirm_delete": "파일 {name}을(를) 삭제하시겠습니까?",
        
        "lib_manager": "라이브러리 관리자",
        "lib_install": "설치",
        "lib_installed": "설치됨",
        "lib_installing": "설치 중...",
        "lib_install_success": "설치 성공!",
        "lib_install_fail": "설치 실패.",
        "lib_needs_rebuild": "APK 재빌드 필요",
        "lib_mode_offline": "오프라인",
        "lib_mode_online": "온라인",
        "lib_mode_hybrid": "하이브리드",
        "lib_category_all": "전체",
        
        "ai_title": "🤖 Zaba AI",
        "ai_provider": "제공자",
        "ai_input_placeholder": "무엇이든 물어보세요...",
        "ai_send": "전송",
        "ai_needs_key": "{provider} API 키가 설정되지 않았습니다.",
        "ai_error": "AI 오류: {error}",
        
        "cancel": "취소",
        "close": "닫기",
        "ok": "확인",
        "yes": "예",
        "no": "아니요",
        "loading": "로딩...",
        "error": "오류",
        "success": "성공",
        "warning": "경고",
    },
    
    # ---- Arabic (ar) ----
    "ar": {
        "app_title": "ZABACODE",
        "app_subtitle": "بيئة تطوير بايثون المحمولة ومساعد الذكاء الاصطناعي",
        "version": "الإصدار",
        
        "status_ready": "جاهز",
        "status_running": "قيد التشغيل...",
        "status_error": "خطأ",
        "status_ok": "تم",
        "line_col": "سطر {line}, عمود {col}",
        
        "new_tab": "جديد",
        "untitled": "بدون_عنوان",
        
        "run": "▶ تشغيل",
        "stop": "⏹ إيقاف",
        "clear": "مسح",
        "check": "فحص الكود",
        
        "sidebar_title": "ZABACODE",
        "files": "📁 الملفات",
        "save": "💾 حفظ",
        "libraries": "📦 المكتبات",
        "ai_keys": "🔑 مفاتيح AI",
        "themes": "🎨 السمات",
        "plugins": "🧩 الإضافات",
        "language": "🌐 اللغة",
        "about": "ℹ️ حول",
        "output": "📤 الإخراج",
        
        "cancel": "إلغاء",
        "close": "إغلاق",
        "ok": "موافق",
        "loading": "جاري التحميل...",
        "error": "خطأ",
        "success": "نجاح",
    },
    
    # ---- Spanish (es) ----
    "es": {
        "app_title": "ZABACODE",
        "app_subtitle": "IDE Python Móvil & Asistente de IA",
        "version": "Versión",
        
        "status_ready": "Listo",
        "status_running": "Ejecutando...",
        "status_error": "Error",
        "status_ok": "Hecho",
        "line_col": "Ln {line}, Col {col}",
        
        "new_tab": "Nueva",
        "untitled": "sin_título",
        
        "run": "▶ EJECUTAR",
        "stop": "⏹ DETENER",
        "clear": "LIMPIAR",
        "check": "VERIFICAR",
        
        "sidebar_title": "ZABACODE",
        "files": "📁 Archivos",
        "save": "💾 Guardar",
        "libraries": "📦 Bibliotecas",
        "ai_keys": "🔑 Claves IA",
        "themes": "🎨 Temas",
        "plugins": "🧩 Plugins",
        "language": "🌐 Idioma",
        "about": "ℹ️ Acerca de",
        "output": "📤 Salida",
        
        "cancel": "Cancelar",
        "close": "Cerrar",
        "ok": "OK",
        "loading": "Cargando...",
        "error": "Error",
        "success": "Éxito",
    },
}

# Supported languages display names
LANGUAGES = {
    "id": "🇮🇩 Bahasa Indonesia",
    "en": "🇬🇧 English",
    "ja": "🇯🇵 日本語",
    "ko": "🇰🇷 한국어",
    "ar": "🇸🇦 العربية",
    "es": "🇪🇸 Español",
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
