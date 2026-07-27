"""Regression coverage for the security and reliability hardening merged in PR #28."""

import inspect
from pathlib import Path

from zabacode.core.executor import MAX_CODE_BYTES, start_interactive_session
from zabacode.core.paths import FILES_DIR
from zabacode.core.security import _get_all_providers
from zabacode.lib_manager import install_library


def test_interactive_runner_rejects_oversized_source() -> None:
    code = "# x\n" * ((MAX_CODE_BYTES // 4) + 1)
    result = start_interactive_session(code)
    assert result["ok"] is False
    assert "large" in result["message"].lower()


def test_desktop_runtime_files_match_documented_project_directory() -> None:
    assert FILES_DIR.resolve() == Path("files").resolve()


def test_custom_provider_is_in_keystore_provider_set() -> None:
    assert "custom" in _get_all_providers()


def test_pip_fallback_does_not_restore_trusted_host_tls_bypass() -> None:
    source = inspect.getsource(install_library)
    executable_lines = [line for line in source.splitlines() if not line.lstrip().startswith("#")]
    assert "--trusted-host" not in "\n".join(executable_lines)


def test_invalid_library_name_type_returns_controlled_error() -> None:
    result = install_library(7)  # type: ignore[arg-type]
    assert result["ok"] is False
    assert "name" in result["message"].lower()


def test_library_install_endpoint_rejects_non_string_name() -> None:
    from zabacode.web_app import app
    from zabacode.core.security import AUTH_TOKEN

    client = app.test_client()
    response = client.post(
        "/api/libraries/install",
        json={"name": 7},
        headers={"X-Zabacode-Token": AUTH_TOKEN},
    )
    assert response.status_code == 400
    assert response.get_json()["ok"] is False
