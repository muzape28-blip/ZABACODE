import builtins
_orig_input = builtins.input
def _safe_input(prompt=""):
    try:
        return _orig_input(prompt)
    except EOFError:
        return ""
builtins.input = _safe_input

prices = [1, 2]
print(prices[9])