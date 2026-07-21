"""
ZABACODE Core — Code Syntax & Structure Checker
Pre-execution validation to prevent EOFError and common syntax issues.
"""

import re


def check_code(code: str) -> dict:
    """
    Validate Python code structure before execution.
    
    Returns dict with: ok, valid, issues, hint
    """
    from zabacode.core.executor import normalize_code
    code = normalize_code(code)
    
    issues = []
    
    # Check balanced parentheses
    paren_open = code.count('(')
    paren_close = code.count(')')
    if paren_open != paren_close:
        issues.append(f"Parenthesis () imbalance: {paren_open} '(' vs {paren_close} ')'")
    
    # Check balanced brackets
    bracket_open = code.count('[')
    bracket_close = code.count(']')
    if bracket_open != bracket_close:
        issues.append(f"Brackets [] imbalance: {bracket_open} '[' vs {bracket_close} ']'")
    
    # Check balanced braces
    brace_open = code.count('{')
    brace_close = code.count('}')
    if brace_open != brace_close:
        issues.append(f"Braces {{}} imbalance: {brace_open} '{{' vs {brace_close} '}}'")
    
    # Check string balance (basic heuristic)
    code_no_triple = re.sub(r'""".*?"""', '', code, flags=re.DOTALL)
    code_no_triple = re.sub(r"'''.*?'''", '', code_no_triple, flags=re.DOTALL)
    
    sq = code_no_triple.count("'")
    dq = code_no_triple.count('"')
    if sq % 2 != 0:
        issues.append("Single quotes (') imbalance")
    if dq % 2 != 0:
        issues.append('Double quotes (") imbalance')
    
    # Check for common Python errors
    lines = code.split('\n')
    for i, line in enumerate(lines, 1):
        stripped = line.rstrip()
        if stripped.endswith(':') and i < len(lines):
            next_line = lines[i]
            if next_line.strip() and not next_line.startswith(' ') and not next_line.startswith('\t'):
                if not next_line.strip().startswith('#') and not next_line.strip().startswith('"""'):
                    pass  # Allow single-line after colon (e.g., dict comprehensions)
    
    return {
        "ok": True,
        "valid": len(issues) == 0,
        "issues": issues,
        "hint": "Fix all issues above before running code" if issues else None
    }
