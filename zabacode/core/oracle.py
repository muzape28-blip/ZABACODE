"""
ZABACODE Core — ZABA ORACLE: Offline Code Intelligence

The IDE claims to be offline-first, yet its AI assistant dies the moment the
network does. The Oracle fixes that: a fully local, zero-dependency code
intelligence engine that keeps working in airplane mode, on a dead SIM, or when
every provider is rate-limited.

It never phones home. It never needs an API key. It cannot be paywalled.

Two capabilities:

  1. ``humanize_traceback()`` — turns a raw Python traceback into a plain-language
     explanation with a concrete fix. Mobile screens are small and tracebacks are
     hostile to beginners; this is the single highest-value offline feature.

  2. ``offline_reply()`` — a rule-based tsundere assistant that answers common
     coding questions and reviews the active buffer with real AST analysis.
     Used automatically as a fallback when a cloud provider is unavailable.
"""

import ast
import re

__all__ = ["humanize_traceback", "offline_reply", "analyze_buffer", "ORACLE_SIGNATURE"]

ORACLE_SIGNATURE = "🔮 Zaba Oracle (offline)"


# ---------------------------------------------------------------------------
# 1. Traceback Humanizer
# ---------------------------------------------------------------------------

# (regex, title, explanation template, fix template)
_ERROR_RULES: list[tuple[str, str, str, str]] = [
    (
        r"NameError: name '([^']+)' is not defined",
        "You used something that doesn't exist yet",
        "Python reached `{0}` but nothing with that name had been created.",
        "Check the spelling, or define `{0} = ...` before this line. If it comes from a "
        "library, you forgot the `import`.",
    ),
    (
        r"ModuleNotFoundError: No module named '([^']+)'",
        "Library not installed",
        "The package `{0}` isn't available in this environment.",
        "Open the Library Manager and install `{0}`. If it needs a C extension, it must be "
        "added to buildozer.spec and the APK rebuilt.",
    ),
    (
        r"IndentationError: (.+)",
        "Your indentation is off",
        "Python uses indentation to define blocks, and this line doesn't line up: {0}.",
        "Make every line in the same block use the same indentation — pick 4 spaces and "
        "never mix them with tabs.",
    ),
    (
        r"TypeError: unsupported operand type\(s\) for (.+?): '([^']+)' and '([^']+)'",
        "You mixed incompatible types",
        "You tried `{0}` between a `{1}` and a `{2}`, which Python refuses to guess about.",
        "Convert one side first — e.g. `int(value)` or `str(value)` — so both sides match.",
    ),
    (
        r"TypeError: '([^']+)' object is not subscriptable",
        "That value can't be indexed",
        "You wrote something like `x[0]`, but `x` is a `{0}` and doesn't support indexing.",
        "Check what the variable actually holds. Functions need `()` to be called; only "
        "sequences like list/tuple/str/dict accept `[...]`.",
    ),
    (
        r"TypeError: (.+?)\(\) missing (\d+) required positional argument",
        "A function call is missing arguments",
        "`{0}()` needs {1} more argument(s) than you passed.",
        "Look at the function's `def` line and supply every parameter that has no default.",
    ),
    (
        r"IndexError: list index out of range",
        "You reached past the end of a list",
        "You asked for an index that doesn't exist — a list of 3 items only has indexes 0, 1, 2.",
        "Guard with `if i < len(my_list):`, or loop with `for item in my_list:` and skip "
        "indexes entirely.",
    ),
    (
        r"KeyError: (.+)",
        "That dictionary key doesn't exist",
        "You looked up {0} in a dict that has no such key.",
        "Use `my_dict.get(key)` to get `None` instead of crashing, or check `if key in my_dict:` first.",
    ),
    (
        r"ZeroDivisionError",
        "Division by zero",
        "Something divided by zero, which is mathematically undefined.",
        "Check the divisor before dividing: `if divisor != 0:`.",
    ),
    (
        r"ValueError: invalid literal for int\(\) with base 10: '([^']*)'",
        "That text isn't a number",
        "`int()` was given `'{0}'`, which contains characters that aren't digits.",
        "Strip whitespace with `.strip()`, or validate with `.isdigit()` before converting.",
    ),
    (
        r"AttributeError: '([^']+)' object has no attribute '([^']+)'",
        "That method or property doesn't exist",
        "A `{0}` has no `{1}`.",
        "Check the spelling, or confirm the variable holds the type you expect — "
        "`print(type(x))` settles it fast.",
    ),
    (
        r"SyntaxError: (?:invalid syntax|unexpected EOF|'\(' was never closed)",
        "Python couldn't parse your code",
        "There's a structural typo — usually an unclosed bracket, a missing `:`, or `=` used "
        "where `==` was meant.",
        "Look at the reported line *and the one above it*: unclosed brackets are reported late.",
    ),
    (
        r"RecursionError",
        "Infinite recursion",
        "A function kept calling itself until Python gave up.",
        "Every recursive function needs a base case that returns without recursing.",
    ),
    (
        r"FileNotFoundError: .*'([^']+)'",
        "File not found",
        "Python couldn't find `{0}` in the working directory.",
        "Check the filename, or create the file first. Relative paths resolve against the "
        "ZABACODE files/ folder.",
    ),
    (
        r"UnboundLocalError: .*'([^']+)'",
        "Local variable used before assignment",
        "`{0}` is assigned somewhere in this function, so Python treats it as local — but you "
        "read it before that assignment ran.",
        "Add `global {0}` if you meant the outer variable, or initialise it at the top of the function.",
    ),
]


def humanize_traceback(stderr: str, line_offset: int = 0) -> dict:
    """Translate a Python traceback into a plain-language explanation.

    ``line_offset`` subtracts the prelude the executor injects, so the reported
    line matches what the user actually sees in the editor.

    Returns ``{"ok": bool, "title", "what", "fix", "line", "raw_error"}``.
    ``ok`` is False when nothing recognisable was found.
    """
    if not stderr or not stderr.strip():
        return {"ok": False}

    # The final non-empty line carries the exception type and message.
    lines = [ln for ln in stderr.strip().split("\n") if ln.strip()]
    error_line = lines[-1].strip()

    # Locate the offending user line number (last "line N" wins — deepest frame).
    line_no = None
    for m in re.finditer(r'line (\d+)', stderr):
        line_no = int(m.group(1))
    if line_no is not None and line_offset:
        line_no = max(1, line_no - line_offset)

    for pattern, title, what_tpl, fix_tpl in _ERROR_RULES:
        match = re.search(pattern, stderr)
        if match:
            groups = match.groups()
            try:
                what = what_tpl.format(*groups)
                fix = fix_tpl.format(*groups)
            except (IndexError, KeyError):
                what, fix = what_tpl, fix_tpl
            return {
                "ok": True,
                "title": title,
                "what": what,
                "fix": fix,
                "line": line_no,
                "raw_error": error_line,
            }

    # Unknown error: still give the user the useful parts.
    return {
        "ok": True,
        "title": "Something went wrong",
        "what": error_line,
        "fix": "Read the last line of the traceback first — it names the actual problem. "
               "The lines above show how execution got there.",
        "line": line_no,
        "raw_error": error_line,
    }


# ---------------------------------------------------------------------------
# 2. Offline buffer analysis (real AST work, no network)
# ---------------------------------------------------------------------------

def analyze_buffer(code: str) -> dict:
    """Statically analyse the editor buffer: structure, smells, complexity."""
    if not code or not code.strip():
        return {"ok": False, "message": "The editor is empty."}

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {
            "ok": False,
            "syntax_error": True,
            "message": f"Syntax error on line {e.lineno}: {e.msg}",
            "line": e.lineno,
        }

    functions: list[dict] = []
    classes: list[dict] = []
    imports: list[str] = []
    notes: list[str] = []
    loop_depth = max_loop_depth = 0
    bare_excepts = 0
    todo_count = len(re.findall(r"#\s*(TODO|FIXME|HACK)", code, re.IGNORECASE))

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            args = len(node.args.args)
            body_len = len(node.body)
            functions.append({"name": node.name, "line": node.lineno, "args": args})
            if args > 5:
                notes.append(f"`{node.name}()` takes {args} arguments — consider grouping them "
                             f"into a dataclass or dict.")
            if body_len > 50:
                notes.append(f"`{node.name}()` is {body_len} statements long. Splitting it will "
                             f"make it far easier to debug on a phone screen.")
            if not ast.get_docstring(node) and not node.name.startswith("_"):
                notes.append(f"`{node.name}()` has no docstring — future-you will thank you.")
        elif isinstance(node, ast.ClassDef):
            classes.append({"name": node.name, "line": node.lineno})
        elif isinstance(node, ast.Import):
            imports.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
        elif isinstance(node, ast.ExceptHandler) and node.type is None:
            bare_excepts += 1

    # Nesting depth of loops — a decent proxy for cognitive load.
    def depth(node, current=0):
        nonlocal max_loop_depth
        for child in ast.iter_child_nodes(node):
            nxt = current + 1 if isinstance(child, (ast.For, ast.While)) else current
            max_loop_depth = max(max_loop_depth, nxt)
            depth(child, nxt)

    depth(tree)
    loop_depth = max_loop_depth

    if bare_excepts:
        notes.append(f"{bare_excepts} bare `except:` block(s) — these swallow Ctrl-C and hide real "
                     f"bugs. Catch a specific exception instead.")
    if loop_depth >= 3:
        notes.append(f"Loops nested {loop_depth} deep. Extracting the inner body into a function "
                     f"usually makes this readable again.")
    if todo_count:
        notes.append(f"{todo_count} TODO/FIXME marker(s) still in the file.")

    return {
        "ok": True,
        "lines": len(code.split("\n")),
        "functions": functions,
        "classes": classes,
        "imports": sorted(set(i for i in imports if i)),
        "loop_depth": loop_depth,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# 3. Offline tsundere assistant
# ---------------------------------------------------------------------------

_TSUNDERE_OPENERS = [
    "Hmph. Fine, I'll look at it.",
    "Don't get the wrong idea — I was going to check anyway.",
    "You're lucky I don't need the internet to do this.",
    "Again? Alright, alright.",
]

_KNOWLEDGE: list[tuple[tuple[str, ...], str]] = [
    (
        ("list comprehension", "listcomp", "comprehension"),
        "`[expr for item in iterable if condition]`. It builds a list in one pass and is faster "
        "than appending in a loop.\n\n"
        "```python\nsquares = [n * n for n in range(10) if n % 2 == 0]\n```",
    ),
    (
        ("read file", "read a file", "open file", "write file", "file handling",
         "reading file", "writing file", "save file", "load file"),
        "Always use a context manager so the file closes even if something raises:\n\n"
        "```python\nwith open('data.txt', 'r', encoding='utf-8') as f:\n    content = f.read()\n```",
    ),
    (
        ("dictionary", "dict "),
        "Use `.get()` when a key might be missing — it returns `None` instead of raising "
        "`KeyError`:\n\n```python\nvalue = config.get('debug', False)\n```",
    ),
    (
        ("class", "oop", "object oriented", "inheritance", "__init__"),
        "```python\nclass Robot:\n    def __init__(self, name):\n        self.name = name\n\n"
        "    def greet(self):\n        return f'Beep. I am {self.name}.'\n```\n"
        "`__init__` runs on creation; `self` is the instance.",
    ),
    (
        ("try/except", "try except", "exception", "error handling", "catch error"),
        "Catch the *specific* thing you expect:\n\n"
        "```python\ntry:\n    value = int(user_input)\nexcept ValueError:\n"
        "    print('That was not a number.')\n```\n"
        "A bare `except:` also catches Ctrl-C. Don't.",
    ),
    (
        ("f-string", "format string", "string format"),
        "f-strings are the modern way:\n\n```python\nname = 'Zaba'\nprint(f'Hello {name}, "
        "{len(name)} chars')\n```\nThey evaluate expressions inline and are the fastest option.",
    ),
    (
        ("loop", "for ", "while "),
        "Iterate the object directly instead of indexing:\n\n```python\nfor item in items:\n"
        "    print(item)\n\nfor i, item in enumerate(items):\n    print(i, item)\n```",
    ),
    (
        ("matplotlib", "plot a", "plot ", "chart", "graph", "visualiz", "visualis"),
        "Save instead of `show()` on Android — ZABACODE picks the image up automatically:\n\n"
        "```python\nimport matplotlib\nmatplotlib.use('Agg')\nimport matplotlib.pyplot as plt\n"
        "plt.plot([1, 2, 3])\nplt.savefig('out.png')\n```",
    ),
    (
        ("faster", "optimize", "performance", "slow"),
        "Three things first: use comprehensions over append-loops, `set` for membership tests "
        "(O(1) vs O(n) for lists), and `''.join(parts)` instead of `+=` in a loop.",
    ),
    (
        ("input", "stdin", "user input"),
        "`input()` returns a string, always convert it:\n\n```python\nage = int(input('Age: '))\n```\n"
        "Use the Interactive Run mode so your program can actually receive input.",
    ),
]


def _match_knowledge(question: str) -> str | None:
    q = question.lower()
    for keywords, answer in _KNOWLEDGE:
        if any(k in q for k in keywords):
            return answer
    return None


def offline_reply(message: str, code: str = "") -> dict:
    """Answer without any network. Always returns ``ok: True`` — never leaves the user stranded."""
    msg = (message or "").strip()
    opener = _TSUNDERE_OPENERS[len(msg) % len(_TSUNDERE_OPENERS)]

    if not msg:
        return {"ok": True, "reply": f"{opener}\n\nYou didn't actually ask anything.",
                "source": ORACLE_SIGNATURE, "offline": True}

    lower = msg.lower()

    # "why did this crash?" — feed it the traceback
    if any(w in lower for w in ("traceback", "error:", "exception", "crash")) and len(msg) > 40:
        human = humanize_traceback(msg)
        if human.get("ok"):
            where = f" (line {human['line']})" if human.get("line") else ""
            return {
                "ok": True,
                "reply": f"{opener}\n\n**{human['title']}**{where}\n\n{human['what']}\n\n"
                         f"**Fix:** {human['fix']}",
                "source": ORACLE_SIGNATURE,
                "offline": True,
            }

    # "review my code" / "what's wrong"
    if any(w in lower for w in ("review", "check my", "what's wrong", "whats wrong",
                                "improve", "refactor", "explain my", "analyze")):
        analysis = analyze_buffer(code)
        if not analysis.get("ok"):
            return {"ok": True, "reply": f"{opener}\n\n{analysis.get('message')}",
                    "source": ORACLE_SIGNATURE, "offline": True}

        parts = [
            opener,
            "",
            f"**{analysis['lines']} lines** · {len(analysis['functions'])} function(s) · "
            f"{len(analysis['classes'])} class(es) · max loop depth {analysis['loop_depth']}",
        ]
        if analysis["notes"]:
            parts.append("")
            parts.append("Things I'd change:")
            parts += [f"- {n}" for n in analysis["notes"]]
        else:
            parts.append("")
            parts.append("...It's actually clean. Don't let it go to your head.")
        return {"ok": True, "reply": "\n".join(parts), "source": ORACLE_SIGNATURE, "offline": True}

    # Knowledge base lookup
    answer = _match_knowledge(lower)
    if answer:
        return {"ok": True, "reply": f"{opener}\n\n{answer}",
                "source": ORACLE_SIGNATURE, "offline": True}

    return {
        "ok": True,
        "reply": f"{opener}\n\nI'm running offline, so my range is limited — I handle error "
                 f"explanations, code review, and Python fundamentals without a network.\n\n"
                 f"Try: *\"review my code\"*, paste a traceback, or ask about loops, files, "
                 f"classes, dicts, or f-strings.\n\n"
                 f"For anything deeper, connect a provider in Settings. No key required for me, "
                 f"though — I don't work for a subscription.",
        "source": ORACLE_SIGNATURE,
        "offline": True,
    }
