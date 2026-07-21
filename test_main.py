"""
ZABACODE v1.0.0 — Comprehensive Unit Tests (Kivy Native Edition)

Run: pytest test_main.py -v
"""

import json
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure the project root is in sys.path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from zabacode import __version__
from zabacode.core.executor import execute_code_isolated, normalize_code, MAX_CODE_BYTES
from zabacode.core.checker import check_code
from zabacode.core.file_manager import (
    secure_filename, list_files, save_file, read_file, delete_file, FILES_DIR
)
from zabacode.core.security import AUTH_TOKEN, verify_token, xor_cipher, xor_decipher, load_keys, save_key
from zabacode.lib_manager import (
    KNOWN_LIBRARIES, is_package_installed, get_all_libraries, install_library,
    get_library_info, _PACKAGE_NAME_RE
)
from zabacode.themes.definitions import THEMES, DEFAULT_THEME, get_theme, list_themes
from zabacode.i18n.translations import i18n, TRANSLATIONS, LANGUAGES
from zabacode.plugins.registry import (
    get_all_plugins, toggle_plugin, is_plugin_active, get_snippets, MARKETPLACE_PLUGINS
)
from zabacode.core.ai_provider import PROVIDER_HANDLERS, PROVIDER_INFO, ALLOWED_PROVIDERS


# ===================================================================
# Test Code Execution Engine
# ===================================================================

class TestCodeExecution:
    """Test code execution & isolation."""
    
    def test_simple_print(self):
        result = execute_code_isolated('print("hello")')
        assert result["ok"] is True
        assert "hello" in result["stdout"]
    
    def test_syntax_error(self):
        result = execute_code_isolated('print("missing quote')
        assert result["ok"] is False
        assert "SyntaxError" in result["stderr"] or "syntax" in result["stderr"].lower()
    
    def test_timeout(self):
        result = execute_code_isolated('while True: pass', timeout=2)
        assert result["timeout"] is True
        assert result["ok"] is False
    
    def test_import_standard_lib(self):
        result = execute_code_isolated('import sys, os\nprint("ok:", os.path.exists("_active_run.py"))')
        assert result["ok"] is True
    
    def test_windows_line_endings_normalized(self):
        code_windows = 'print("test 1")\r\nprint("test 2")\r\n'
        normalized = normalize_code(code_windows)
        assert '\r\n' not in normalized
        assert '\r' not in normalized
        result = execute_code_isolated(code_windows)
        assert result["ok"] is True
    
    def test_trailing_whitespace_normalized(self):
        code = 'print("test")   \nprint("next")   \n'
        normalized = normalize_code(code)
        lines = normalized.split('\n')
        assert lines[0] == 'print("test")'
        assert lines[1] == 'print("next")'
    
    def test_bom_removed(self):
        code_with_bom = '\ufeffprint("hello")'
        normalized = normalize_code(code_with_bom)
        assert not normalized.startswith('\ufeff')
        assert normalized.startswith('print')
    
    def test_code_too_large(self):
        result = execute_code_isolated("x = 1\n" * 100000)  # Large code
        assert result["ok"] is False
    
    def test_non_string_code(self):
        result = execute_code_isolated(12345)
        assert result["ok"] is False
    
    def test_file_resolution(self):
        result = execute_code_isolated('from pathlib import Path\nprint(Path(__file__).name)')
        assert result["ok"] is True


# ===================================================================
# Test Code Checker
# ===================================================================

class TestCodeChecker:
    """Test code syntax validation."""
    
    def test_valid_code(self):
        result = check_code("print('hello')\nprint('world')")
        assert result["valid"] is True
        assert len(result["issues"]) == 0
    
    def test_unbalanced_parens(self):
        result = check_code("print('hello'")
        assert result["valid"] is False
        assert any("Parenthesis" in i or "()" in i for i in result["issues"])
    
    def test_unbalanced_brackets(self):
        result = check_code("x = [1, 2, 3")
        assert result["valid"] is False
        assert any("[]" in i or "Brackets" in i for i in result["issues"])
    
    def test_unbalanced_braces(self):
        result = check_code("d = {1: 2")
        assert result["valid"] is False
    
    def test_unbalanced_quotes(self):
        result = check_code("x = 'hello")
        assert result["valid"] is False


# ===================================================================
# Test File Manager & Security
# ===================================================================

class TestFileManager:
    """Test file operations and path traversal prevention."""
    
    def test_secure_filename_valid(self):
        assert secure_filename("test") == "test.py"
        assert secure_filename("script.py") == "script.py"
    
    def test_secure_filename_path_traversal(self):
        assert secure_filename("../etc/passwd") is None
        assert secure_filename("..\\secret") is None
    
    def test_secure_filename_dotfile(self):
        assert secure_filename(".zabacode_keys") is None
        assert secure_filename(".env") is None
    
    def test_secure_filename_null_bytes(self):
        assert secure_filename("test\x00.py") is None
    
    def test_secure_filename_empty(self):
        assert secure_filename("") is None
        assert secure_filename(".py") is None
    
    def test_secure_filename_system_file(self):
        assert secure_filename("_active_run") is None
    
    def test_save_and_read_file(self):
        result = save_file("test_unit_file", "print('hello from test')")
        assert result["ok"] is True
        
        read_result = read_file("test_unit_file.py")
        assert read_result["ok"] is True
        assert "hello from test" in read_result["content"]
        
        # Cleanup
        delete_file("test_unit_file.py")
    
    def test_delete_nonexistent_file(self):
        result = delete_file("nonexistent_xyz_12345.py")
        assert result["ok"] is False
    
    def test_read_nonexistent_file(self):
        result = read_file("nonexistent_xyz_12345.py")
        assert result["ok"] is False


# ===================================================================
# Test Security Module
# ===================================================================

class TestSecurity:
    """Test authentication and encryption."""
    
    def test_auth_token_exists(self):
        assert AUTH_TOKEN is not None
        assert len(AUTH_TOKEN) >= 16
    
    def test_verify_valid_token(self):
        assert verify_token(AUTH_TOKEN) is True
    
    def test_verify_invalid_token(self):
        assert verify_token("invalid_token_12345") is False
        assert verify_token("") is False
    
    def test_xor_cipher_roundtrip(self):
        original = "Hello, ZABACODE! 🔥"
        encrypted = xor_cipher(original, "test_key")
        decrypted = xor_decipher(encrypted, "test_key")
        assert decrypted == original
    
    def test_xor_decipher_invalid(self):
        result = xor_decipher("not_valid_base64!!!", "key")
        assert result == ""


# ===================================================================
# Test Library Manager
# ===================================================================

class TestLibraryManager:
    """Test library management system."""
    
    def test_known_libraries_not_empty(self):
        assert len(KNOWN_LIBRARIES) >= 30  # We expanded significantly
    
    def test_libraries_have_required_fields(self):
        for name, info in KNOWN_LIBRARIES.items():
            assert "tier" in info, f"Missing 'tier' in {name}"
            assert "category" in info, f"Missing 'category' in {name}"
            assert "mode" in info, f"Missing 'mode' in {name}"
            assert "reason" in info, f"Missing 'reason' in {name}"
            assert info["tier"] in ["runtime", "buildtime"], f"Invalid tier in {name}"
            assert info["mode"] in ["offline", "online", "hybrid"], f"Invalid mode in {name}"
    
    def test_required_libraries_present(self):
        required = ["requests", "beautifulsoup4", "numpy", "tinydb", "fastapi", "rich",
                    "flask", "sympy", "pydantic", "pillow", "pyjwt"]
        for lib in required:
            assert lib in KNOWN_LIBRARIES, f"Missing library: {lib}"
    
    def test_get_all_libraries(self):
        libs = get_all_libraries()
        assert isinstance(libs, dict)
        assert len(libs) >= 30
        for name, info in libs.items():
            assert "installed" in info
    
    def test_get_library_info(self):
        info = get_library_info("requests")
        assert info is not None
        assert info["mode"] == "online"
    
    def test_get_nonexistent_library(self):
        info = get_library_info("nonexistent_package_xyz")
        assert info is None
    
    def test_offline_libraries_exist(self):
        offline_libs = [name for name, info in KNOWN_LIBRARIES.items() if info["mode"] == "offline"]
        assert len(offline_libs) >= 5  # At least 5 offline libs
    
    def test_online_libraries_exist(self):
        online_libs = [name for name, info in KNOWN_LIBRARIES.items() if info["mode"] == "online"]
        assert len(online_libs) >= 5  # At least 5 online libs
    
    def test_hybrid_libraries_exist(self):
        hybrid_libs = [name for name, info in KNOWN_LIBRARIES.items() if info["mode"] == "hybrid"]
        assert len(hybrid_libs) >= 3  # At least 3 hybrid libs
    
    def test_buildtime_libraries(self):
        buildtime = [name for name, info in KNOWN_LIBRARIES.items() if info["tier"] == "buildtime"]
        assert len(buildtime) >= 3
    
    def test_package_name_regex(self):
        assert _PACKAGE_NAME_RE.fullmatch("requests") is not None
        assert _PACKAGE_NAME_RE.fullmatch("my-package") is not None
        assert _PACKAGE_NAME_RE.fullmatch("") is None
        assert _PACKAGE_NAME_RE.fullmatch("../../../etc") is None
    
    def test_install_invalid_package(self):
        result = install_library("")
        assert result["ok"] is False
    
    def test_install_buildtime_package(self):
        result = install_library("numpy")
        assert result["ok"] is False
        assert result.get("needs_rebuild") is True


# ===================================================================
# Test Themes
# ===================================================================

class TestThemes:
    """Test theme system."""
    
    def test_themes_not_empty(self):
        assert len(THEMES) >= 6
    
    def test_default_theme_exists(self):
        assert DEFAULT_THEME in THEMES
    
    def test_theme_has_required_colors(self):
        required_keys = ["bg", "bg_panel", "border", "border_bright", "text",
                        "text_bright", "text_dim", "err", "ai", "editor_bg",
                        "editor_fg", "line_number_fg"]
        for name, theme in THEMES.items():
            for key in required_keys:
                assert key in theme, f"Missing '{key}' in theme '{name}'"
    
    def test_theme_colors_are_tuples(self):
        for name, theme in THEMES.items():
            for key, value in theme.items():
                if key not in ["display_name", "icon"]:
                    assert isinstance(value, tuple), f"{name}.{key} is not tuple"
                    assert len(value) == 4, f"{name}.{key} doesn't have 4 components"
    
    def test_get_theme(self):
        theme = get_theme("retro")
        assert theme is not None
        assert "bg" in theme
    
    def test_get_nonexistent_theme(self):
        assert get_theme("nonexistent_theme") is None
    
    def test_list_themes(self):
        themes = list_themes()
        assert isinstance(themes, dict)
        assert "retro" in themes
        assert "cyberpunk" in themes
    
    def test_new_themes_present(self):
        """v1.0.0 added new themes."""
        for t in ["tokyo_night", "one_dark", "gruvbox", "catppuccin"]:
            assert t in THEMES, f"New theme '{t}' missing"


# ===================================================================
# Test i18n (Internationalization)
# ===================================================================

class TestI18n:
    """Test multi-language support."""
    
    def test_default_language(self):
        assert i18n.lang == "id"
    
    def test_translation_keys_present(self):
        # Both en and id should have the same core keys
        id_keys = set(TRANSLATIONS["id"].keys())
        en_keys = set(TRANSLATIONS["en"].keys())
        # en should be a superset or equal
        assert len(id_keys & en_keys) >= 30
    
    def test_translate_id(self):
        i18n.lang = "id"
        assert i18n.t("run") == "▶ JALANKAN"
    
    def test_translate_en(self):
        i18n.lang = "en"
        assert i18n.t("run") == "▶ RUN"
    
    def test_translate_with_kwargs(self):
        i18n.lang = "en"
        result = i18n.t("about_version", version="1.0.0")
        assert "1.0.0" in result
    
    def test_fallback_to_en(self):
        i18n.lang = "ko"  # Korean has fewer translations
        result = i18n.t("app_title")
        assert result == "ZABACODE"
    
    def test_fallback_to_key(self):
        result = i18n.t("nonexistent_key_xyz_12345")
        assert result == "nonexistent_key_xyz_12345"
    
    def test_set_language(self):
        i18n.set_language("en")
        assert i18n.lang == "en"
        i18n.set_language("id")  # Reset
    
    def test_invalid_language_not_set(self):
        i18n.set_language("id")
        i18n.set_language("invalid_lang")
        assert i18n.lang == "id"  # Should not change
    
    def test_available_languages(self):
        langs = i18n.get_available_languages()
        assert "id" in langs
        assert "en" in langs
        assert "ja" in langs
    
    def test_min_4_languages(self):
        """v1.0.0 supports at least 4 languages."""
        assert len(LANGUAGES) >= 4


# ===================================================================
# Test Plugin System
# ===================================================================

class TestPlugins:
    """Test plugin registry and marketplace."""
    
    def test_plugins_not_empty(self):
        assert len(MARKETPLACE_PLUGINS) >= 4
    
    def test_core_plugins_present(self):
        core = ["auto_formatter", "snippet_pack", "syntax_linter", "symbol_bar"]
        for pid in core:
            assert pid in MARKETPLACE_PLUGINS, f"Core plugin '{pid}' missing"
    
    def test_new_v1_plugins(self):
        """v1.0.0 added new plugins."""
        new_plugins = ["code_minifier", "json_formatter", "regex_tester", "todo_manager"]
        for pid in new_plugins:
            assert pid in MARKETPLACE_PLUGINS, f"New plugin '{pid}' missing"
    
    def test_plugin_has_required_fields(self):
        for pid, info in MARKETPLACE_PLUGINS.items():
            assert "id" in info
            assert "name" in info
            assert "description" in info
            assert "version" in info
            assert "mode" in info
    
    def test_toggle_plugin(self):
        # Toggle off
        result = toggle_plugin("auto_formatter")
        assert result["ok"] is True
        assert result["active"] is False
        
        # Toggle back on
        result = toggle_plugin("auto_formatter")
        assert result["ok"] is True
        assert result["active"] is True
    
    def test_toggle_nonexistent_plugin(self):
        result = toggle_plugin("nonexistent_plugin")
        assert result["ok"] is False
    
    def test_is_plugin_active(self):
        assert is_plugin_active("auto_formatter") is True
    
    def test_get_all_plugins(self):
        plugins = get_all_plugins()
        assert isinstance(plugins, dict)
        for pid, info in plugins.items():
            assert "active" in info
    
    def test_snippets_available(self):
        snippets = get_snippets()
        assert isinstance(snippets, dict)
        assert len(snippets) >= 5
    
    def test_snippets_have_code(self):
        for sid, snippet in get_snippets().items():
            assert "name" in snippet
            assert "code" in snippet
            assert len(snippet["code"]) > 0


# ===================================================================
# Test AI Provider System
# ===================================================================

class TestAIProviders:
    """Test AI provider configuration."""
    
    def test_providers_not_empty(self):
        assert len(PROVIDER_HANDLERS) >= 4
    
    def test_core_providers(self):
        for p in ["openrouter", "gemini", "groq", "mistral"]:
            assert p in PROVIDER_HANDLERS, f"Provider '{p}' missing"
    
    def test_new_v1_providers(self):
        """v1.0.0 added DeepSeek and Ollama."""
        assert "deepseek" in PROVIDER_HANDLERS
        assert "ollama" in PROVIDER_HANDLERS
    
    def test_provider_info(self):
        for pid, info in PROVIDER_INFO.items():
            assert "name" in info
            assert "mode" in info
            assert info["mode"] in ["online", "offline"]
    
    def test_allowed_providers(self):
        for p in PROVIDER_HANDLERS:
            assert p in ALLOWED_PROVIDERS
    
    def test_ollama_is_offline(self):
        assert PROVIDER_INFO["ollama"]["mode"] == "offline"


# ===================================================================
# Test Version
# ===================================================================

class TestVersion:
    """Test version info."""
    
    def test_version_is_1_0_0(self):
        assert __version__ == "1.0.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
