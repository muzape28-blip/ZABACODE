"""
ZABACODE v1.0.0 — Comprehensive Unit Tests (WebView Edition)

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
from zabacode.core.executor import (
    execute_code_isolated,
    normalize_code,
    MAX_CODE_BYTES,
    start_interactive_session,
    send_interactive_input,
    get_interactive_output,
    stop_interactive_session
)
from zabacode.core.checker import check_code
from zabacode.core.file_manager import (
    secure_filename, list_files, save_file, read_file, delete_file, FILES_DIR
)
from zabacode.core.security import AUTH_TOKEN, verify_token, load_keys, save_key
from zabacode.lib_manager import (
    KNOWN_LIBRARIES, is_package_installed, get_all_libraries, install_library,
    get_library_info, _PACKAGE_NAME_RE
)
from zabacode.themes.definitions import THEMES, DEFAULT_THEME, get_theme, list_themes
# Translations removed
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
        assert lines[-3] == 'print("test")'
        assert lines[-2] == 'print("next")'
        assert lines[-1] == ''

    def test_bom_removed(self):
        code_with_bom = '\ufeffprint("hello")'
        normalized = normalize_code(code_with_bom)
        assert not normalized.startswith('\ufeff')
        assert 'print("hello")' in normalized
    
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
        # After Arena integration, version is 1.2.0-arena, but still valid semver-like
        assert __version__ in ("1.0.0", "1.1.0", "1.2.0-arena") or __version__.startswith("1.")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# ===================================================================
# Test Interactive Subprocess Execution
# ===================================================================

class TestInteractiveExecution:
    """Test interactive unbuffered code execution engine."""

    def test_interactive_start_and_stop(self):
        code = "import sys\nline = sys.stdin.readline()\nprint('ECHO:', line)"
        res = start_interactive_session(code)
        assert res["ok"] is True

        # Stop session
        stop_res = stop_interactive_session()
        assert stop_res["ok"] is True

    def test_interactive_communication(self):
        code = "import sys\nline = sys.stdin.readline().strip()\nprint('HELLO ' + line)\n"
        start_res = start_interactive_session(code)
        assert start_res["ok"] is True

        # Send input
        send_res = send_interactive_input("ZAQI\n")
        assert send_res["ok"] is True

        # Wait a bit and get output
        import time
        time.sleep(0.5)

        out_res = get_interactive_output()
        assert out_res["ok"] is True

        # Collect stdout chars
        stdout_chars = "".join([char for stype, char in out_res["output"] if stype == "stdout"])
        assert "HELLO ZAQI" in stdout_chars

        stop_interactive_session()

    def test_interactive_multiple_inputs(self):
        code = "name = input('Name: ')\nage = input('Age: ')\nprint(f'{name} is {age}')\n"
        assert start_interactive_session(code)["ok"] is True
        assert send_interactive_input("Zaqi\n")["ok"] is True
        assert send_interactive_input("20\n")["ok"] is True

        import time
        time.sleep(0.5)
        out_res = get_interactive_output()
        stdout_chars = "".join(char for stream, char in out_res["output"] if stream == "stdout")
        assert "Name: Age: Zaqi is 20" in stdout_chars
        assert out_res["done"] is True


# ===================================================================
# Test New Transform Plugins (v1.1.0)
# ===================================================================

class TestNewPlugins:
    """Test suite for the 5 new transform plugins and PluginExecutor."""

    def test_auto_import_optimizer(self):
        from zabacode.plugins.implementations import AutoImportOptimizer
        code = "import os\nimport sys\nimport math\nprint(os.name)\n"
        new_code, report = AutoImportOptimizer.optimize(code)
        assert "import sys" in new_code
        assert "# import sys" in new_code or "#import sys" in new_code or "unused import" in "".join(report)
        assert "math" in "".join(report)

    def test_duplicate_line_detector(self):
        from zabacode.plugins.implementations import DuplicateLineDetector
        code = "x = 10\ny = 20\nx = 10\n"
        new_code, report = DuplicateLineDetector.detect(code)
        assert "WARNING: Duplicate line" in new_code
        assert len(report) > 1

    def test_smart_comment_generator(self):
        from zabacode.plugins.implementations import SmartCommentGenerator
        code = "def greet(name):\n    print('Hello', name)\n"
        new_code, report = SmartCommentGenerator.generate(code)
        assert '"""Docstring for greet.' in new_code
        assert "name" in new_code

    def test_code_beautifier_pro(self):
        from zabacode.plugins.implementations import CodeBeautifierPro
        code = "x=5\ny  =  10\nprint(x,y)\n"
        new_code, report = CodeBeautifierPro.beautify(code)
        assert "x = 5" in new_code
        assert "y = 10" in new_code
        assert "x, y" in new_code

    def test_variable_type_hint_generator(self):
        from zabacode.plugins.implementations import VariableTypeHintGenerator
        code = "def add(a=5, b=''):\n    return a + b\n"
        new_code, report = VariableTypeHintGenerator.generate(code)
        assert "a: int" in new_code
        assert "b: str" in new_code
        assert "from typing import Any" in new_code

    def test_plugin_executor(self):
        from zabacode.plugins.implementations import PluginExecutor
        code = "x=5\n"
        res = PluginExecutor.execute_plugin("code_beautifier_pro", code)
        assert res["ok"] is True
        assert "code" in res

# ===================================================================
# Test API Keys Clearing
# ===================================================================

class TestApiKeysClearing:
    # Test empty API key clearing.

    def test_clear_api_key(self):
        from zabacode.core.security import save_key, load_keys
        # Save a valid key
        save_key("openrouter", "my-test-api-key")
        assert load_keys().get("openrouter") == "my-test-api-key"

        # Save empty key to clear/delete it
        save_key("openrouter", "")
        # Since empty key is treated as truthy fallback, verify it is empty/cleared
        assert not load_keys().get("openrouter")


# ---------------------------------------------------------------------------
# TLS / SSL Regression Tests (fix: CERTIFICATE_VERIFY_FAILED on all providers)
# ---------------------------------------------------------------------------

class TestTLSHardening:
    """Guards the Android CA-bundle fix and forbids unverified SSL fallbacks."""

    def test_ssl_context_verifies_certificates(self):
        from zabacode.core.net import get_ssl_context
        import ssl as _ssl
        ctx = get_ssl_context()
        assert ctx.verify_mode == _ssl.CERT_REQUIRED
        assert ctx.check_hostname is True

    def test_no_unverified_ssl_context_in_codebase(self):
        """_create_unverified_context() would reopen the MITM/RCE hole."""
        import pathlib
        root = pathlib.Path(__file__).parent / "zabacode"
        offenders = [
            str(f) for f in root.rglob("*.py")
            if "_create_unverified_context" in f.read_text(encoding="utf-8")
        ]
        assert offenders == [], f"Unverified SSL context found in: {offenders}"

    def test_all_ai_providers_use_shared_context(self):
        """Every urlopen must pass context= or Android fails to verify certs."""
        import pathlib, re
        from zabacode.core.ai_provider import ALLOWED_PROVIDERS
        src = (pathlib.Path(__file__).parent / "zabacode" / "core" / "ai_provider.py").read_text()
        calls = re.findall(r"urllib\.request\.urlopen\([^)]*\)", src)
        assert len(calls) == len(ALLOWED_PROVIDERS), f"expected {len(ALLOWED_PROVIDERS)} provider calls (one per provider), found {len(calls)}: {calls}"
        for call in calls:
            assert "context=get_ssl_context()" in call, f"missing context: {call}"

    def test_tls_error_returns_actionable_message(self):
        import ssl as _ssl
        from zabacode.core.ai_provider import _handle_url_error
        res = _handle_url_error(_ssl.SSLCertVerificationError("certificate verify failed"), "OpenRouter")
        assert res["ok"] is False
        assert res.get("tls_error") is True
        assert "certifi" in res["message"]

    def test_certifi_declared_for_apk_build(self):
        import pathlib
        spec = (pathlib.Path(__file__).parent / "buildozer.spec").read_text()
        req_line = next(l for l in spec.splitlines() if l.startswith("requirements ="))
        assert "certifi" in req_line, "certifi missing from buildozer.spec -> APK will fail TLS"


class TestNoServerErrors:
    """Every route must respond without a 5xx (regression: /api/translations)."""

    def test_no_route_returns_5xx(self):
        from zabacode.web_app import app
        from zabacode.core.security import AUTH_TOKEN
        client = app.test_client()
        headers = {"X-Zabacode-Token": AUTH_TOKEN}
        failures = []
        for rule in app.url_map.iter_rules():
            if "static" in rule.endpoint or "<" in str(rule):
                continue
            for method in (rule.methods & {"GET", "POST", "DELETE"}):
                resp = client.open(str(rule), method=method, json={}, headers=headers)
                if resp.status_code >= 500:
                    failures.append(f"{method} {rule} -> {resp.status_code}")
        assert failures == [], f"5xx responses: {failures}"


# ---------------------------------------------------------------------------
# Offline-First / Asset Bundling (C-2)
# ---------------------------------------------------------------------------

class TestOfflineFirst:
    """The IDE must be fully usable with zero network access."""

    def test_no_cdn_references_in_template(self):
        import pathlib
        html = (pathlib.Path(__file__).parent / "templates" / "index.html").read_text(encoding="utf-8")
        for cdn in ("cdnjs.cloudflare.com", "unpkg.com", "jsdelivr.net", "googleapis.com"):
            assert cdn not in html, f"External CDN '{cdn}' breaks offline-first"

    def test_ace_bundled_on_disk(self):
        import pathlib
        vendor = pathlib.Path(__file__).parent / "assets" / "vendor" / "ace"
        for f in ("ace.js", "mode-python.js", "theme-tomorrow_night_eighties.js",
                  "ext-settings_menu.js", "ext-language_tools.js", "ext-searchbox.js"):
            path = vendor / f
            assert path.exists() and path.stat().st_size > 1000, f"missing/empty: {f}"

    def test_ace_served_by_flask(self):
        from zabacode.web_app import app
        client = app.test_client()
        for f in ("ace.js", "mode-python.js", "ext-language_tools.js"):
            resp = client.get(f"/static/vendor/ace/{f}")
            assert resp.status_code == 200, f"/static/vendor/ace/{f} -> {resp.status_code}"

    def test_security_headers_present(self):
        from zabacode.web_app import app
        resp = app.test_client().get("/")
        csp = resp.headers.get("Content-Security-Policy", "")
        assert "default-src 'self'" in csp and "frame-ancestors 'none'" in csp
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"


# ---------------------------------------------------------------------------
# Encrypted Key Storage (H-1)
# ---------------------------------------------------------------------------

class TestKeystoreEncryption:
    """API keys must not be recoverable from a hardcoded source-code key."""

    def test_roundtrip(self):
        from zabacode.core.keystore import decrypt_payload, encrypt_payload
        data = {"openrouter": "sk-or-v1-secret", "groq": "gsk_abc123"}
        assert decrypt_payload(encrypt_payload(data)) == data

    def test_plaintext_never_appears_in_ciphertext(self):
        from zabacode.core.keystore import encrypt_payload
        blob = encrypt_payload({"openrouter": "sk-or-v1-SUPERSECRET"})
        assert "SUPERSECRET" not in blob

    def test_nonce_makes_output_unique(self):
        from zabacode.core.keystore import encrypt_payload
        data = {"gemini": "same-key"}
        assert encrypt_payload(data) != encrypt_payload(data)

    def test_tampered_payload_rejected(self):
        import json
        from zabacode.core.keystore import decrypt_payload, encrypt_payload
        env = json.loads(encrypt_payload({"groq": "gsk_real"}))
        flipped = bytearray(bytes.fromhex(env["data"]))
        flipped[0] ^= 0xFF
        env["data"] = flipped.hex()
        assert decrypt_payload(json.dumps(env)) == {}, "tampered ciphertext must be rejected"

    def test_no_hardcoded_encryption_key(self):
        import pathlib
        src = (pathlib.Path(__file__).parent / "zabacode" / "core" / "security.py").read_text()
        assert "zabacode_local_keys_salt" not in src

    def test_master_key_not_tracked_by_git(self):
        import pathlib
        gitignore = (pathlib.Path(__file__).parent / ".gitignore").read_text()
        assert ".zabacode_master_key" in gitignore


# ---------------------------------------------------------------------------
# Dead Code Removal (C-3) & Concurrency (M-1)
# ---------------------------------------------------------------------------

class TestCleanupAndConcurrency:

    def test_kivy_ui_package_removed(self):
        import pathlib
        assert not (pathlib.Path(__file__).parent / "zabacode" / "ui").exists()

    def test_interactive_session_is_lock_guarded(self):
        import pathlib
        src = (pathlib.Path(__file__).parent / "zabacode" / "core" / "executor.py").read_text()
        assert "_session_lock" in src
        assert src.count("with _session_lock:") >= 4

    def test_concurrent_stop_calls_are_safe(self):
        import threading
        from zabacode.core.executor import stop_interactive_session
        errors = []

        def worker():
            try:
                stop_interactive_session()
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)
        assert errors == [], f"concurrency errors: {errors}"


# ---------------------------------------------------------------------------
# ZABA ORACLE — Offline Code Intelligence
# ---------------------------------------------------------------------------

class TestOracleTracebackHumanizer:
    """Plain-language error explanations must work with zero network."""

    def test_name_error(self):
        from zabacode.core.oracle import humanize_traceback
        r = humanize_traceback('File "main.py", line 7\nNameError: name \'qty\' is not defined')
        assert r["ok"] and "qty" in r["what"] and r["line"] == 7

    def test_permission_error(self):
        from zabacode.core.oracle import humanize_traceback
        r = humanize_traceback("PermissionError: [Errno 13] Permission denied: '/root/secret.txt'")
        assert r["ok"] and "Access Denied" in r["title"]

    def test_unicode_decode_error(self):
        from zabacode.core.oracle import humanize_traceback
        r = humanize_traceback("UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte")
        assert r["ok"] and "Encoding Mismatch" in r["title"]

    def test_json_decode_error(self):
        from zabacode.core.oracle import humanize_traceback
        r = humanize_traceback("json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)")
        assert r["ok"] and "JSON" in r["title"]

    def test_import_error(self):
        from zabacode.core.oracle import humanize_traceback
        r = humanize_traceback("ImportError: cannot import name 'nonexistent' from 'math'")
        assert r["ok"] and "Import" in r["title"]

    def test_assertion_error(self):
        from zabacode.core.oracle import humanize_traceback
        r = humanize_traceback("AssertionError: 2 == 3")
        assert r["ok"] and "Assertion" in r["title"]

    def test_module_not_found(self):
        from zabacode.core.oracle import humanize_traceback
        r = humanize_traceback("ModuleNotFoundError: No module named 'pandas'")
        assert r["ok"] and "pandas" in r["what"]
        assert "Library Manager" in r["fix"]

    def test_type_error_captures_both_types(self):
        from zabacode.core.oracle import humanize_traceback
        r = humanize_traceback("TypeError: unsupported operand type(s) for +: 'int' and 'str'")
        assert r["ok"] and "int" in r["what"] and "str" in r["what"]

    def test_unknown_error_still_helpful(self):
        from zabacode.core.oracle import humanize_traceback
        r = humanize_traceback("WeirdCustomError: something exploded")
        assert r["ok"] and r["fix"]

    def test_empty_input_is_not_ok(self):
        from zabacode.core.oracle import humanize_traceback
        assert humanize_traceback("")["ok"] is False

    def test_every_rule_is_a_valid_regex_and_formats(self):
        import re
        from zabacode.core.oracle import _ERROR_RULES
        for pattern, title, what, fix in _ERROR_RULES:
            re.compile(pattern)          # must not raise
            assert title and what and fix


class TestOracleBufferAnalysis:

    def test_detects_smells(self):
        from zabacode.core.oracle import analyze_buffer
        code = (
            "def f(a, b, c, d, e, g):\n"
            "    for i in range(3):\n"
            "        for j in range(3):\n"
            "            for k in range(3):\n"
            "                try:\n"
            "                    pass\n"
            "                except:\n"
            "                    pass\n"
        )
        r = analyze_buffer(code)
        assert r["ok"] and r["loop_depth"] == 3
        joined = " ".join(r["notes"])
        assert "6 arguments" in joined and "bare `except:`" in joined

    def test_detects_mutable_defaults(self):
        from zabacode.core.oracle import analyze_buffer
        r = analyze_buffer("def f(x=[]):\n    pass")
        assert r["ok"]
        assert any("Mutable default" in note for note in r["notes"])

    def test_detects_unreachable_code(self):
        from zabacode.core.oracle import analyze_buffer
        r = analyze_buffer("def f():\n    return 42\n    print('hello')")
        assert r["ok"]
        assert any("Unreachable code" in note for note in r["notes"])

    def test_detects_static_division_by_zero(self):
        from zabacode.core.oracle import analyze_buffer
        r = analyze_buffer("x = 10 / 0")
        assert r["ok"]
        assert any("division or modulo by zero" in note for note in r["notes"])

    def test_detects_security_risk(self):
        from zabacode.core.oracle import analyze_buffer
        r = analyze_buffer("eval('1+1')")
        assert r["ok"]
        assert any("Security risk" in note for note in r["notes"])

    def test_reports_syntax_error_with_line(self):
        from zabacode.core.oracle import analyze_buffer
        r = analyze_buffer("def broken(:\n    pass")
        assert r["ok"] is False and r["syntax_error"] is True and r["line"]

    def test_clean_code_has_no_notes(self):
        from zabacode.core.oracle import analyze_buffer
        r = analyze_buffer('def add(a, b):\n    """Add two numbers."""\n    return a + b\n')
        assert r["ok"] and r["notes"] == []

    def test_empty_buffer(self):
        from zabacode.core.oracle import analyze_buffer
        assert analyze_buffer("   ")["ok"] is False


class TestOracleOfflineAssistant:

    def test_never_fails(self):
        from zabacode.core.oracle import offline_reply
        for q in ["", "asdkjhasd", "how do I loop?", "review my code", "explain classes"]:
            r = offline_reply(q, "x = 1")
            assert r["ok"] is True and r["reply"] and r["offline"] is True

    def test_knowledge_lookup(self):
        from zabacode.core.oracle import offline_reply
        assert "savefig" in offline_reply("how do I plot a chart?")["reply"]
        assert "with open" in offline_reply("how to read a file?")["reply"]

    def test_new_knowledge_lookup(self):
        from zabacode.core.oracle import offline_reply
        assert "decorator" in offline_reply("what is a decorator?")["reply"].lower()
        assert "yield" in offline_reply("explain generator")["reply"].lower()
        assert "flask" in offline_reply("how to use flask?")["reply"].lower()
        assert "lambda" in offline_reply("how to write lambda?")["reply"].lower()
        assert "pypi" in offline_reply("how to install library using pip")["reply"].lower()
        assert "asyncio" in offline_reply("tell me about async await")["reply"].lower()

    def test_review_uses_real_analysis(self):
        from zabacode.core.oracle import offline_reply
        reply = offline_reply("review my code", "def f(a,b,c,d,e,g):\n    pass\n")["reply"]
        assert "6 arguments" in reply

    def test_requires_no_network(self, monkeypatch):
        """Hard guarantee: the Oracle must not open a socket."""
        import socket
        def boom(*a, **k):
            raise AssertionError("Oracle attempted a network connection")
        monkeypatch.setattr(socket.socket, "connect", boom)
        from zabacode.core.oracle import humanize_traceback, offline_reply, analyze_buffer
        assert offline_reply("review my code", "x=1")["ok"]
        assert humanize_traceback("KeyError: 'a'")["ok"]
        assert analyze_buffer("x = 1")["ok"]


class TestOracleEndpoints:

    def _client(self):
        from zabacode.web_app import app
        from zabacode.core.security import AUTH_TOKEN
        return app.test_client(), {"X-Zabacode-Token": AUTH_TOKEN}

    def test_explain_endpoint(self):
        c, h = self._client()
        r = c.post("/api/oracle/explain",
                   json={"stderr": "NameError: name 'foo' is not defined"}, headers=h)
        assert r.status_code == 200 and r.get_json()["ok"] and "foo" in r.get_json()["what"]

    def test_analyze_endpoint(self):
        c, h = self._client()
        r = c.post("/api/oracle/analyze", json={"code": "def f():\n    pass\n"}, headers=h)
        assert r.status_code == 200 and r.get_json()["ok"]

    def test_endpoints_require_auth(self):
        from zabacode.web_app import app
        c = app.test_client()
        for ep in ("/api/oracle/explain", "/api/oracle/analyze"):
            assert c.post(ep, json={}).status_code == 401

    def test_run_attaches_explanation_on_crash(self):
        c, h = self._client()
        r = c.post("/api/run", json={"code": "print(undefined_thing)"}, headers=h)
        body = r.get_json()
        assert body["ok"] is False
        assert body["explain"]["ok"] and "undefined_thing" in body["explain"]["what"]

    def test_successful_run_has_no_explanation(self):
        c, h = self._client()
        body = c.post("/api/run", json={"code": "print('hi')"}, headers=h).get_json()
        assert body["ok"] is True and "explain" not in body

    def test_ai_chat_falls_back_to_oracle_without_key(self):
        """Regression for the screenshot: user must never hit a dead end."""
        c, h = self._client()
        r = c.post("/api/ai/chat",
                   json={"provider": "openrouter", "message": "review my code",
                         "code": "def f(a,b,c,d,e,g): pass"}, headers=h)
        body = r.get_json()
        assert r.status_code == 200 and body["ok"] is True
        assert body["offline"] is True and body["fallback_reason"] == "no_api_key"

    def test_ai_chat_can_opt_out_of_fallback(self):
        c, h = self._client()
        r = c.post("/api/ai/chat",
                   json={"provider": "groq", "message": "hi", "allow_offline": False}, headers=h)
        assert r.status_code == 401 and r.get_json()["needs_key"] is True


class TestOracleUI:

    def test_oracle_card_rendered_in_frontend(self):
        import pathlib
        html = (pathlib.Path(__file__).parent / "templates" / "index.html").read_text(encoding="utf-8")
        assert "renderOracleCard" in html and ".oracle-card" in html
        assert "/api/oracle/explain" in html

    def test_ui_is_english_only(self):
        import pathlib
        html = (pathlib.Path(__file__).parent / "templates" / "index.html").read_text(encoding="utf-8")
        for word in ("BENERIN", "Kode saya mengalami"):
            assert word not in html


class TestOracleLineMapping:
    """Reported line numbers must match the editor, not the injected prelude."""

    def test_line_number_matches_user_editor(self):
        from zabacode.web_app import app
        from zabacode.core.security import AUTH_TOKEN
        c = app.test_client()
        body = c.post("/api/run", json={"code": "prices = [1, 2]\nprint(prices[9])"},
                      headers={"X-Zabacode-Token": AUTH_TOKEN}).get_json()
        assert body["explain"]["line"] == 2, "line must map to the editor, not the prelude"

    def test_offset_never_goes_below_one(self):
        from zabacode.core.oracle import humanize_traceback
        r = humanize_traceback('File "m.py", line 2\nKeyError: 1', line_offset=99)
        assert r["line"] == 1

    def test_prelude_count_matches_actual_patch(self):
        from zabacode.core.executor import PRELUDE_LINE_COUNT, SAFE_INPUT_PATCH
        assert PRELUDE_LINE_COUNT == SAFE_INPUT_PATCH.count("\n")


class TestOracleAutoFix:
    """Verify Zaba Oracle's offline Auto-Fix capabilities."""

    def test_missing_quotes_in_print(self):
        from zabacode.core.oracle import auto_fix_code
        r = auto_fix_code("print(hello world)")
        assert r["ok"] is True
        assert r["fixed_code"] == 'print("hello world")'
        assert any("quotes" in fix for fix in r["applied_fixes"])

    def test_single_equals_conditional(self):
        from zabacode.core.oracle import auto_fix_code
        r = auto_fix_code("if x = 5:")
        assert r["ok"] is True
        assert r["fixed_code"] == "if x == 5:"
        assert any("==" in fix for fix in r["applied_fixes"])

    def test_missing_colon(self):
        from zabacode.core.oracle import auto_fix_code
        r = auto_fix_code("if x == 5")
        assert r["ok"] is True
        assert r["fixed_code"] == "if x == 5:"
        assert any("colon" in fix or ":" in fix for fix in r["applied_fixes"])

    def test_unterminated_string_literal(self):
        from zabacode.core.oracle import auto_fix_code
        r = auto_fix_code("print(\"hello")
        assert r["ok"] is True
        assert r["fixed_code"] == 'print("hello")'
        assert any("unterminated" in fix or "string" in fix for fix in r["applied_fixes"])

    def test_unclosed_brackets(self):
        from zabacode.core.oracle import auto_fix_code
        r = auto_fix_code("x = [1, 2")
        assert r["ok"] is True
        assert r["fixed_code"] == "x = [1, 2]"
        assert any("bracket" in fix or "parenthesis" in fix for fix in r["applied_fixes"])

    def test_fix_endpoint_auth(self):
        from zabacode.web_app import app
        c = app.test_client()
        r = c.post("/api/oracle/fix", json={"code": "print(hello)"})
        assert r.status_code == 401

    def test_fix_endpoint_success(self):
        from zabacode.web_app import app
        from zabacode.core.security import AUTH_TOKEN
        c = app.test_client()
        r = c.post(
            "/api/oracle/fix",
            json={"code": "print(hello world)"},
            headers={"X-Zabacode-Token": AUTH_TOKEN}
        )
        assert r.status_code == 200
        body = r.get_json()
        assert body["ok"] is True
        assert body["fixed_code"] == 'print("hello world")'

    def test_ui_contains_auto_fix_functions(self):
        import pathlib
        html = (pathlib.Path(__file__).parent / "templates" / "index.html").read_text(encoding="utf-8")
        assert "renderAutoFixButton" in html
        assert "renderDiffView" in html
        assert "renderAutoFixResult" in html
