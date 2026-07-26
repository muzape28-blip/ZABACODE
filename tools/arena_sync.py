#!/usr/bin/env python3
"""
ZABACODE x Arena.ai — Workspace Sync Tool

This tool verifies that the local checkout is fully integrated
with Arena Agent Mode and prepares it for GitHub push.

Usage:
    python tools/arena_sync.py --verify
    python tools/arena_sync.py --status
    python tools/arena_sync.py --test-arena
    python tools/arena_sync.py --prepare-push

Arena Integration: feature/arena-integration
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def run(cmd, cwd=ROOT):
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return result

def check_status():
    print("=== ⚡ ZABACODE x Arena — Git Status ===\n")
    for cmd in [
        "git remote -v",
        "git branch --show-current",
        "git status --short",
        "git log --oneline -5",
    ]:
        r = run(cmd)
        print(f"$ {cmd}\n{r.stdout}{r.stderr}\n")

def verify_integration():
    print("=== 🔍 Verifying Arena Integration ===\n")
    ok = True

    # Check provider file
    provider_path = ROOT / "zabacode" / "core" / "ai_provider.py"
    text = provider_path.read_text(encoding="utf-8")
    checks = [
        ("arena" in text and "ALLOWED_PROVIDERS" in text, "ALLOWED_PROVIDERS contains arena"),
        ("def call_arena" in text, "call_arena function exists"),
        ('"arena": call_arena' in text or "'arena': call_arena" in text or '"arena":' in text and "call_arena" in text, "arena in PROVIDER_HANDLERS"),
        ('"arena"' in text and "PROVIDER_INFO" in text, "arena in PROVIDER_INFO"),
    ]
    # Actually second check for handlers more robust
    has_handler = "PROVIDER_HANDLERS" in text and "arena" in text.split("PROVIDER_HANDLERS")[1][:500]
    
    for passed, desc in checks:
        status = "✅" if passed else "❌"
        print(f"{status} {desc}")
        if not passed:
            ok = False

    # Try import
    try:
        sys.path.insert(0, str(ROOT))
        from zabacode.core.ai_provider import ALLOWED_PROVIDERS, PROVIDER_HANDLERS, call_arena
        print(f"\n✅ Import OK — providers: {sorted(ALLOWED_PROVIDERS)}")
        if "arena" not in ALLOWED_PROVIDERS:
            print("❌ arena not in ALLOWED_PROVIDERS")
            ok = False
        if "arena" not in PROVIDER_HANDLERS:
            print("❌ arena not in PROVIDER_HANDLERS")
            ok = False
        
        # Test offline
        res = call_arena("", "hello", "print('hi')", "arena-offline-v1")
        if res.get("ok") and "ARENA INTEGRATION" in res.get("reply", ""):
            print("✅ Arena offline mode works")
            print(f"\nSample reply preview:\n{res['reply'][:400]}...\n")
        else:
            print(f"❌ Arena offline response invalid: {res}")
            ok = False
    except Exception as e:
        print(f"❌ Import/test failed: {e}")
        import traceback
        traceback.print_exc()
        ok = False

    # Check template
    tpl = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    tpl_checks = [
        ("arena" in tpl.lower(), "arena in index.html"),
        ("arena-offline-v1" in tpl, "arena-offline-v1 model exists"),
    ]
    for passed, desc in tpl_checks:
        status = "✅" if passed else "❌"
        print(f"{status} {desc}")
        if not passed:
            ok = False

    # Check workflow
    wf = ROOT / ".github" / "workflows" / "arena-integration.yml"
    if wf.exists():
        print(f"✅ Workflow exists: {wf}")
    else:
        print(f"❌ Workflow missing: {wf}")
        ok = False

    print("\n" + ("✅ INTEGRATION VERIFIED" if ok else "❌ INTEGRATION FAILED"))
    return ok

def test_arena():
    sys.path.insert(0, str(ROOT))
    from zabacode.core.ai_provider import call_arena
    print("=== ⚡ Testing Arena Provider ===\n")
    cases = [
        ("", "Explain this code", "def add(a,b):\n    return a+b", "arena-offline-v1"),
        ("", "How to fix IndexError?", "my_list = [1,2,3]\nprint(my_list[10])", "arena-oracle-enhanced"),
        ("https://example.com/v1", "Test custom endpoint (should fallback offline)", "x=1", "arena-custom-endpoint"),
    ]
    for api_key, msg, code, model in cases:
        print(f"--- Model: {model} ---")
        res = call_arena(api_key, msg, code, model)
        print(f"ok={res.get('ok')} offline={res.get('offline')} provider={res.get('provider')}")
        print(f"Reply preview: {res.get('reply','')[:300]}...\n")

def run_tests():
    print("=== 🧪 Running pytest ===\n")
    r = run("python -m pytest test_main.py -v --tb=short -k 'not test_timeout' 2>&1 | tail -n 100")
    # Actually run full
    full = run("python -m pytest test_main.py -v")
    print(full.stdout[-5000:])
    print(full.stderr[-2000:])
    if full.returncode == 0:
        print("\n✅ All tests passed")
    else:
        print("\n❌ Tests failed")
    return full.returncode == 0

def prepare_push():
    print("=== 📦 Prepare Push to GitHub ===\n")
    print("This workspace is in /home/user/ZABACODE")
    print("Branch: feature/arena-integration")
    print("\nTo push to GitHub (replace YOUR_TOKEN):")
    print("""
    git remote set-url origin https://<YOUR_TOKEN>@github.com/muzape28-blip/ZABACODE.git
    git push origin feature/arena-integration

    Then create PR on GitHub:
    Title: feat: Arena.ai Integration (7th provider, offline-first)
    Body: See INTEGRATION_ARENA.md
    Base: main <- feature/arena-integration
    """)
    print("\nOr generate patch:")
    print("    git format-patch main --stdout > /tmp/arena-integration.patch")
    print("\nChanged files:")
    r = run("git diff --name-only main...HEAD")
    print(r.stdout)
    r2 = run("git status --short")
    print("\nUntracked/modified:")
    print(r2.stdout)

def main():
    parser = argparse.ArgumentParser(description="ZABACODE x Arena Sync Tool")
    parser.add_argument("--status", action="store_true", help="Show git status")
    parser.add_argument("--verify", action="store_true", help="Verify integration")
    parser.add_argument("--test-arena", action="store_true", help="Test arena provider")
    parser.add_argument("--test", action="store_true", help="Run pytest")
    parser.add_argument("--prepare-push", action="store_true", help="Show push instructions")
    parser.add_argument("--all", action="store_true", help="Run all checks")
    args = parser.parse_args()

    if not any(vars(args).values()):
        args.all = True

    if args.all or args.status:
        check_status()
    if args.all or args.verify:
        verify_integration()
    if args.all or args.test_arena:
        test_arena()
    if args.all or args.test:
        run_tests()
    if args.all or args.prepare_push:
        prepare_push()

if __name__ == "__main__":
    main()
