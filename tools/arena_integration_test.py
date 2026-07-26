"""
Test Arena Integration — standalone test file
Run: pytest tools/arena_integration_test.py -v
"""

def test_arena_provider_registered():
    from zabacode.core.ai_provider import ALLOWED_PROVIDERS, PROVIDER_HANDLERS, PROVIDER_INFO
    assert "arena" in ALLOWED_PROVIDERS
    assert "arena" in PROVIDER_HANDLERS
    assert "arena" in PROVIDER_INFO
    assert PROVIDER_INFO["arena"]["mode"] == "offline"

def test_arena_offline_no_key():
    from zabacode.core.ai_provider import call_arena
    res = call_arena("", "Explain this", "print('hello')", "arena-offline-v1")
    assert res["ok"] is True
    assert "ARENA INTEGRATION" in res["reply"]
    assert res["offline"] is True
    assert "ZABACODE" in res["reply"]

def test_arena_with_code_context_analysis():
    from zabacode.core.ai_provider import call_arena
    code = """
def foo(x):
    if x == 1:
        if x == 2:
            if x == 3:
                print("deep")
"""
    res = call_arena("", "Review my code", code, "arena-oracle-enhanced")
    assert res["ok"] is True
    # Should include analysis because code has deep nesting
    assert "Arena Static Analysis" in res["reply"] or "ARENA INTEGRATION" in res["reply"]

def test_arena_custom_endpoint_fallback():
    from zabacode.core.ai_provider import call_arena
    # Use invalid URL — should fallback to offline, not crash
    res = call_arena("https://invalid.example.local/v1", "hello", "x=1", "arena-custom-endpoint")
    # Should still return ok because offline fallback
    assert res["ok"] is True
    assert res["provider"] == "arena"

def test_allowed_providers_count():
    from zabacode.core.ai_provider import ALLOWED_PROVIDERS
    # Now 7 providers
    assert len(ALLOWED_PROVIDERS) == 7
