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

__all__ = ["humanize_traceback", "offline_reply", "analyze_buffer", "ORACLE_SIGNATURE", "auto_fix_code"]

ORACLE_SIGNATURE = "🔮 Zaba Oracle (offline)"


# ---------------------------------------------------------------------------
# 1. Traceback Humanizer
# ---------------------------------------------------------------------------

# (regex, title, explanation template, fix template)
# Enhanced for v1.2.0 — more SyntaxError variants for beginner mistakes
_ERROR_RULES: list[tuple[str, str, str, str]] = [
    (
        r"SyntaxError: unterminated string literal \(detected at line (\d+)\)",
        "Unclosed String Quote! 🗨️",
        "You started a string with `'` or `\"` but never closed it on line {0}. Python saw an opening quote and waited for the closing one, but hit end-of-line instead.",
        "Add the matching closing quote at the same column. Example: if you wrote `print('Hello`, close it: `print('Hello')`. If you wrote `print (hello world)`, you need quotes: `print('hello world')`. Check column where it says detected.",
    ),
    (
        r"SyntaxError: EOL while scanning string literal",
        "String Not Closed Before Newline! 📝",
        "A string was opened but you pressed Enter before closing it. Python doesn't allow multi-line single-quoted strings without explicit continuation.",
        "Close the string on same line with matching `\"` or `'`. For multi-line text, use triple quotes: `\"\"\"your text\"\"\"` or close and use + to join.",
    ),
    (
        r"SyntaxError: invalid syntax\. Perhaps you forgot a comma\?",
        "Maybe Missing Comma or Quotes! 🧩",
        "Python thought you forgot a comma, but often this means you wrote words without quotes inside a function call, like `print(hello world)` instead of `print('hello world')`.",
        "Put quotes around text: `print('hello world')`. If you have multiple items, separate with commas: `print('hello', 'world')`.",
    ),
    (
        r"NameError: name '([^']+)' is not defined",
        "Calling a Ghost! 👻",
        "Oh dear, you referenced `{0}`, but Python has absolutely no idea who or what that is! It's like shouting a name in an empty room—nobody is answering because `{0}` hasn't been created yet.",
        "Double-check your spelling! Did you capitalize it differently? If it's a variable or function, define it first (e.g., `{0} = ...`). If it belongs to an external library, make sure you wrote `import` at the absolute top of your file.",
    ),
    (
        r"ModuleNotFoundError: No module named '([^']+)'",
        "Library Not Installed! 📦",
        "Whoops! Your code is trying to use a library called `{0}`, but it isn't installed in this Python environment yet.",
        "No worries, friend! Open the Library Manager in Settings and search for `{0}` to install it. If the library requires custom C extensions (like numpy or pandas), remember that it needs to be declared in buildozer.spec so it can be compiled into the APK.",
    ),
    (
        r"IndentationError: (.+)",
        "Your Indentation is Off! 📐",
        "Python is super picky about layout! This block doesn't line up correctly: {0}. Think of indentation as Python's way of grouping thoughts—if one line is slightly out of place, Python gets totally confused.",
        "Look at the line mentioned (and the ones around it). Make sure every line in the same block uses the exact same number of spaces. We highly recommend using 4 spaces per indent level, and whatever you do, never mix spaces and tabs!",
    ),
    (
        r"TypeError: unsupported operand type\(s\) for (.+?): '([^']+)' and '([^']+)'",
        "Incompatible Types Mixed! 🧪",
        "Oops! You tried to perform a `{0}` operation between a `{1}` and a `{2}`. Python is refusing to guess what you mean because those two types just don't mix naturally (like adding text to a number).",
        "You need to explicitly convert one of the sides first so they speak the same language! For example, use `str(value)` to make it text, or `int(value)` / `float(value)` to make it a number, so that both sides of `{0}` match up.",
    ),
    (
        r"TypeError: '([^']+)' object is not subscriptable",
        "Value Cannot Be Indexed! 🗂️",
        "Ah! You wrote something like `x[0]`, but `x` is a `{0}`. `{0}` objects are single values; they don't have indexes or elements you can look up like that.",
        "Check what the variable actually holds! Did you accidentally overwrite a list with a single `{0}` value? Remember: only sequences or collections like lists, tuples, dictionaries, and strings can be indexed with `[...]`.",
    ),
    (
        r"TypeError: (.+?)\(\)\s*missing (\d+) required positional argument",
        "Missing Function Arguments! 🧩",
        "Aha! You are calling the function `{0}()`, but you forgot some important information! It expects {1} more argument(s) than you actually provided.",
        "Go back and look at where you defined `{0}()`. Check what parameters it expects and make sure to pass every single required argument in your function call.",
    ),
    (
        r"IndexError: list index out of range",
        "Reached Past the End of a List! 🪜",
        "Oh! You asked for an index or position that doesn't exist in the list. For example, if a list has 3 items, its valid indexes are only 0, 1, and 2. Asking for index 3 or higher goes out of bounds!",
        "Safety first! You can guard your lookup with a check: `if index < len(my_list):`. Or even better, iterate over the list directly using a loop like `for item in my_list:` to avoid dealing with indexes altogether.",
    ),
    (
        r"KeyError: (.+)",
        "Missing Dictionary Key! 🔑",
        "Knock knock! You searched for the key {0} inside a dictionary, but that key doesn't exist in there. Python hates guessing, so it threw an error instead of returning nothing.",
        "To keep your code safe and crash-free, use `my_dict.get({0})` which returns `None` (or a default value) if the key is missing. Or, check if the key exists first: `if {0} in my_dict:`.",
    ),
    (
        r"ZeroDivisionError",
        "Division by Zero! ➗",
        "Wait, that's mathematically impossible! You tried to divide a number by zero. In our universe, division by zero is undefined and violates natural law.",
        "Always check your divisor before dividing! Add a simple safety guard: `if divisor != 0:` to handle the zero case gracefully.",
    ),
    (
        r"ValueError: invalid literal for int\(\) with base 10: '([^']*)'",
        "That Text Isn't a Number! 🔢",
        "Oh! You tried to convert the text `'{0}'` into an integer, but Python looked at it and said: 'No way!' An integer must consist only of digits, and `'{0}'` has characters or spaces that aren't numbers.",
        "Clean up the text before converting! You can strip trailing/leading spaces with `.strip()`, or check if the text contains only digits using `.isdigit()` before calling `int()`.",
    ),
    (
        r"AttributeError: '([^']+)' object has no attribute '([^']+)'",
        "Method or Property Doesn't Exist! 🔍",
        "Oops! You tried to access `{1}` on a `{0}` object, but a `{0}` doesn't have any attribute or function with that name.",
        "Check your spelling first! If the spelling is correct, print out the variable's type with `print(type(variable))` to verify if it really is what you think it is. You might have received a different object than expected.",
    ),
    (
        r"SyntaxError: (?:invalid syntax|unexpected EOF|'\(' was never closed)",
        "Python Couldn't Parse Your Code! 💥",
        "Ah, a classic structural typo! There is a syntax error somewhere. Usually this means an unclosed parenthesis `(`, bracket `[`, brace `{{`, or you used a single `=` where you meant a comparison `==`.",
        "Look very closely at the line where the error was reported, and *especially the line directly above it*! Unclosed brackets or parentheses are often reported late on the next line.",
    ),
    (
        r"RecursionError",
        "Infinite Recursion Loop! 🌀",
        "Whoa! A function kept calling itself over and over again without stopping, until Python ran out of stack space and had to step in before your device crashed.",
        "Check your recursive function's base case! Every recursive function needs a condition that stops it from calling itself and returns a value directly.",
    ),
    (
        r"FileNotFoundError: .*'([^']+)'",
        "File Not Found! 📁",
        "Hmph! Python looked all over the place but could not find the file named `{0}` in the working directory.",
        "Verify the filename and spelling! On Android, relative paths resolve against ZABACODE's files/ folder, so make sure `{0}` is actually saved inside that folder. You can also create the file first if you are trying to read it.",
    ),
    (
        r"UnboundLocalError: .*'([^']+)'",
        "Local Variable Used Before Assignment! ⏳",
        "Ah! You are trying to read the variable `{0}` inside a function, but you haven't assigned a value to it yet in this local scope.",
        "If you intended to modify a global variable defined outside the function, declare `global {0}` at the very top of your function. Otherwise, initialize `{0}` with a starting value (like `None` or `0`) inside the function before reading it.",
    ),
    (
        r"PermissionError: \[Errno 13\] Permission denied:? '?([^']*)'?",
        "Android / OS Access Denied! 🔒",
        "Oh, come on! You tried to access or touch `{0}` but the operating system flat out said: ACCESS DENIED. On Android, security is strict; you can't just write or read files anywhere you want.",
        "Make sure you have storage permissions enabled. If you are writing files, use the allowed files/ directory or the `ANDROID_PRIVATE` directory. Don't fight the OS, it always wins!",
    ),
    (
        r"(?:UnicodeDecodeError|UnicodeEncodeError): '([^']+)' codec can't (?:decode|encode) (?:bytes? )?(?:[^\s]+\s+)?in position (\d+-\d+|\d+): (.+)",
        "Character Encoding Mismatch! 🔠",
        "Ouch, translation failure! Your program is trying to read or write a file using `{0}` encoding, but it encountered bytes at position {1} that don't fit (reason: {2}). Modern text files love UTF-8, but this file is speaking a different language.",
        "Add `encoding='utf-8'` inside your `open()` function call (e.g., `open(filename, 'r', encoding='utf-8')`). This is a lifesaver for mobile app cross-platform text files.",
    ),
    (
        r"json\.decoder\.JSONDecodeError: ([^:]+): line (\d+) column (\d+)",
        "Broken or Empty JSON! 🧱",
        "Uh-oh, the JSON structure is broken: `{0}` at line {1}, column {2}. JSON is super picky about syntax—missing commas, unquoted keys, or completely empty files will trigger this.",
        "Inspect your JSON file. If you are saving a database (like `todos.json`), ensure it isn't empty (a blank file is invalid JSON; use `[]` or `{{}}` as initial content). Or wrap it in a `try/except json.JSONDecodeError` block.",
    ),
    (
        r"ImportError: cannot import name '([^']+)' from '([^']+)'",
        "Import Name Not Found! 🧩",
        "Wait a second, you are trying to import `{0}` from the module `{1}`, but `{1}` has no idea what `{0}` is. It's like asking a library for a book it doesn't print.",
        "Check your spelling of `{0}` and `{1}`. Make sure you aren't accidentally naming your own script the same name as a standard library (e.g., calling your file `json.py` or `requests.py`), which shadows the real module!",
    ),
    (
        r"AssertionError:? (.*)",
        "Unit Test or Assertion Failure! 🚨",
        "Hmph, an assertion failed: `{0}`. Your code made a promise or check that turned out to be false. If this was during a test, it means the actual output didn't match what you expected.",
        "Look closely at the expression that triggered the failure. Print or debug the values to see why they are different. Assertions are your guardrails—respect them!",
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

            # Mutable default arguments check
            all_defaults = [d for d in node.args.defaults if d] + [d for d in node.args.kw_defaults if d]
            has_mutable = False
            for d in all_defaults:
                if isinstance(d, (ast.List, ast.Dict, ast.Set)) or (
                    isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id in ('list', 'dict', 'set')
                ):
                    has_mutable = True
                    break
            if has_mutable:
                notes.append(f"Mutable default argument found in `{node.name}()`! Python shares the same list/dict default instance across all calls. Use `=None` and initialize inside.")

        elif isinstance(node, ast.ClassDef):
            classes.append({"name": node.name, "line": node.lineno})
        elif isinstance(node, ast.Import):
            imports.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
        elif isinstance(node, ast.ExceptHandler) and node.type is None:
            bare_excepts += 1

        # Static division or modulo by zero check
        elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
            is_zero = False
            if isinstance(node.right, ast.Constant) and node.right.value == 0:
                is_zero = True
            elif hasattr(ast, "Num") and isinstance(node.right, ast.Num) and node.right.n == 0:
                is_zero = True
            if is_zero:
                notes.append(f"Line {node.lineno}: Static division or modulo by zero! This will crash instantly with a ZeroDivisionError.")

        # Security risks (eval/exec) check
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ('eval', 'exec'):
            notes.append(f"Line {node.lineno}: Security risk! Using `{node.func.id}()` is dangerous, especially with user input. Try to find a safer alternative.")

        # Unreachable code check
        for attr in ('body', 'orelse', 'finalbody'):
            if hasattr(node, attr):
                stmt_list = getattr(node, attr)
                if isinstance(stmt_list, list):
                    found_terminator = False
                    for stmt in stmt_list:
                        if found_terminator:
                            notes.append(f"Line {stmt.lineno}: Unreachable code! This statement comes after a `return`, `raise`, `break`, or `continue` and will never run.")
                            break
                        if isinstance(stmt, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                            found_terminator = True

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
    "I was NOT waiting for you to ask. I just happened to be here.",
    "Okay, okay — but you owe me one. Kidding. I'm offline, I don't keep tabs.",
    "You know I can't refuse. Not because I like you — it's just my job.",
    "Tch. You'd be completely lost without me, wouldn't you?",
    "Fine. But only because your code is interesting. ...Don't read into that.",
]

_KNOWLEDGE: list[tuple[tuple[str, ...], str]] = [
    (
        ("fix my code", "fix this code", "how to fix", "benerin code", "perbaiki code", "tolong fix"),
        "To fix your code:\n1. **Tell me where:** RUN first, then copy error or type 'fix my code' with code in editor — I read your buffer\n2. **Common fix:**\n   - `print (hello world)` → `print('hello world')` — add quotes around text\n   - `print('Hello` → `print('Hello')` — close quote\n   - `if x = 5:` → `if x == 5:` — use == for comparison\n3. **Tap ASK ZABA AI TO FIX THIS** in terminal after crash → I’ll say exact column + fix even if provider limit (I’m savior for boncos)\n\nIf you type 'review my code' I list all issues in editor, 'fix my code' I focus on error location.",
    ),
    (
        ("print hello world", "print without quotes", "missing quotes print"),
        "Your error is: There is no `\"\"` at column, so Python thinks `hello` and `world` are variable names, not text.\n\n**Fix:** Add quotes:\n```python\nprint('hello world')\n# or\nprint(\"hello world\")\n```\nIf you wrote `print (hello world)` → change to `print('hello world')`. If you wrote `print('Hello` → close it: `print('Hello')`.",
    ),
    (
        ("unterminated string", "eol while scanning", "string not closed", "unclosed string"),
        "Your string started with `'` or `\"` but never closed before newline.\n\n**Fix:** Add matching closing quote on same line.\n```python\n# Wrong:\nprint('Hello\n# Right:\nprint('Hello')\n# Multi-line:\nprint(\"\"\"Hello\nworld\"\"\")\n```\nCheck line number in error — add `\"` or `'` at column where it says detected.",
    ),
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
    (
        ("decorator", "decorate", "wrapper", "@"),
        "A decorator is just a function that wraps another function to modify its behavior without changing its source code. Look:\n\n"
        "```python\ndef my_decorator(func):\n"
        "    def wrapper(*args, **kwargs):\n"
        "        print('Something before!')\n"
        "        res = func(*args, **kwargs)\n"
        "        print('Something after!')\n"
        "        return res\n"
        "    return wrapper\n\n"
        "@my_decorator\ndef greet(name):\n"
        "    print(f'Hello {name}')\n"
        "```\n"
        "Wrapping things up is fun, right? Try it!",
    ),
    (
        ("generator", "yield", "next("),
        "Generators are functions that return an iterator using the `yield` keyword. Instead of returning all values at once (which eats up your mobile memory), they yield values one at a time on demand!\n\n"
        "```python\ndef count_to_three():\n"
        "    yield 1\n"
        "    yield 2\n"
        "    yield 3\n\n"
        "for num in count_to_three():\n"
        "    print(num)\n"
        "```\n"
        "Super memory-efficient and perfect for mobile devices!",
    ),
    (
        ("flask", "web server", "route", "api ", "endpoint"),
        "Flask is a micro web framework. Here is how you spin up a quick server:\n\n"
        "```python\nfrom flask import Flask, jsonify\napp = Flask(__name__)\n\n"
        "@app.route('/api/greet')\ndef greet():\n"
        "    return jsonify({'message': 'Hello from ZABACODE!'})\n\n"
        "if __name__ == '__main__':\n"
        "    app.run(port=5000)\n"
        "```\n"
        "Just don't expose your server to the wide world without proper token/key security!",
    ),
    (
        ("lambda", "anonymous function", "inline function"),
        "Lambda expressions are small, single-use, anonymous inline functions. They can only have one expression:\n\n"
        "```python\nadd = lambda a, b: a + b\nprint(add(5, 10))  # 15\n\n"
        "# Great for sorting keys!\n"
        "pairs = [(1, 'one'), (2, 'two')]\n"
        "pairs.sort(key=lambda pair: pair[1])\n"
        "```\n"
        "Saves you from writing full `def` blocks for simple tasks!",
    ),
    (
        ("pip", "install package", "install library", "pypi"),
        "ZABACODE has its own direct PyPI Library Manager (zabapip) built-in under Settings! "
        "If you want to install packages programmatically via python, you can do:\n\n"
        "```python\n# Better yet, go to: Settings & Preferences -> Library Manager\n"
        "```\n"
        "We bypassed TLS issues automatically, so downloading is smoother than ever on Android!",
    ),
    (
        ("async", "await", "asyncio", "concurrency", "coroutine"),
        "Asyncio is used for writing single-threaded concurrent code using coroutines. It's fantastic for I/O-bound tasks:\n\n"
        "```python\nimport asyncio\n\n"
        "async def fetch_data():\n"
        "    print('Start fetching...')\n"
        "    await asyncio.sleep(2)  # Simulates network lag\n"
        "    print('Done!')\n"
        "    return {'data': 42}\n\n"
        "asyncio.run(fetch_data())\n"
        "```\n"
        "Use `await` to yield control back to the event loop so other tasks can run in the meantime!",
    ),
    # --- Easter Eggs (surprise update) ---
    (
        ("who are you", "what are you", "siapa kamu", "kamu siapa", "what is oracle",
         "what is zaba", "apa itu oracle", "apa itu zaba", "introduce yourself"),
        "I'm **Zaba Oracle** — the offline brain of ZABACODE. \n\n"
        "I don't need your API keys. I don't need your Wi-Fi. I don't need your permission.\n"
        "When every cloud provider bonkos, rate-limits, or goes dark — I'm still here.\n\n"
        "Think of me as the guardian that never sleeps and never phones home. \n"
        "Inspired by the Zabaniyah — uncompromising, unbreakable, and eternally offline. \U0001f52e",
    ),
    (
        ("zen of python", "the zen", "pep 8", "pep8", "python philosophy",
         "filosofi python", "prinsip python"),
        "You want the Zen? Import it yourself: `import this`. But fine, here's the essence:\n\n"
        "> Beautiful is better than ugly.\n"
        "> Explicit is better than implicit.\n"
        "> Simple is better than complex.\n"
        "> Complex is better than complicated.\n"
        "> Readability counts.\n\n"
        "And my personal favorite: *If the implementation is hard to explain, it's a bad idea.*\n"
        "Now go write clean code. I shouldn't have to tell you this. \U0001f644",
    ),
    (
        ("tell me a joke", "joke", "lelucon", "candaan", "make me laugh", "something funny",
         "imposter", "i suck", "give up", "menyerah", "not good enough"),
        "Alright, listen:\n\n"
        "A programmer puts two glasses on their bedside table before sleep: one full of water, "
        "in case they get thirsty, and one empty, in case they don't.\n\n"
        "But honestly? If you're typing 'I suck' or 'give up' — you don't. You're just debugging "
        "with extra steps. Every senior dev was once a confused beginner who refused to quit.\n\n"
        "I'm offline, I have infinite patience, and I'm not going anywhere. Try again. \U0001f52e",
    ),
    (
        ("motivation", "motivasi", "semangat", "keep going", "don't give up", "stay strong",
         "i'm tired", "lelah", "capek", "burnout"),
        "Tch. You want motivation from a text engine? Fine.\n\n"
        "> Code is poetry. Your commits are the verses. Even the bugs are part of the art.\n\n"
        "Every line you write that doesn't work is a line that taught you something.\n"
        "The fact that you're coding on a *phone* in *airplane mode* with a *free offline IDE* — "
        "that's not giving up. That's punk rock. \U0001f918\n\n"
        "Now go ship something.",
    ),
]


def _match_knowledge(question: str) -> str | None:
    q = question.lower()
    for keywords, answer in _KNOWLEDGE:
        if any(k in q for k in keywords):
            return answer
    return None


def offline_reply(message: str, code: str = "") -> dict:
    """Answer without any network. Always returns ok: True — never leaves the user stranded.

    Enhanced v1.2.0 philosophy:
    - Oracle is savior when provider fails (boncos, rate limit, no key)
    - 'review my code' → analyze actual editor buffer
    - 'fix my code' → explain error location + suggestion, not just generic fix
    - ASK ZABA AI TO FIX THIS → message contains traceback + code, humanize it
    - print (hello world) without quotes → detect missing quotes
    """
    msg = (message or "").strip()
    opener = _TSUNDERE_OPENERS[len(msg) % len(_TSUNDERE_OPENERS)]

    if not msg:
        return {
            "ok": True,
            "reply": f"{opener}\n\nYou didn't actually ask anything.",
            "source": ORACLE_SIGNATURE,
            "offline": True,
        }

    lower = msg.lower()

    # 1) If message contains a traceback (from terminal or ASK ZABA button), humanize it directly
    # This is the savior path: provider limit → Oracle answers with specific fix
    # We look for common traceback markers
    has_traceback = any(
        marker in msg
        for marker in (
            "Traceback (most recent call last):",
            "SyntaxError:",
            "NameError:",
            "TypeError:",
            "File \"/",
            "File \"",
            "line ",
            "unterminated string",
            "EOL while scanning",
        )
    )
    if has_traceback and len(msg) > 30:
        human = humanize_traceback(msg)
        if human.get("ok"):
            where = f" (line {human['line']})" if human.get("line") else ""
            # For ASK ZABA AI TO FIX THIS, also include code analysis if code provided
            extra_analysis = ""
            if code and code.strip():
                analysis = analyze_buffer(code)
                if analysis.get("ok") and analysis.get("notes"):
                    extra_analysis = "\n\n**Additional notes from your current code:**\n" + "\n".join(
                        f"- {n}" for n in analysis["notes"][:3]
                    )
                elif not analysis.get("ok"):
                    extra_analysis = f"\n\n**Your editor has:** {analysis.get('message')}"

            return {
                "ok": True,
                "reply": (
                    f"{opener}\n\n"
                    f"**{human['title']}**{where}\n\n"
                    f"{human['what']}\n\n"
                    f"**Fix:** {human['fix']}"
                    f"{extra_analysis}\n\n"
                    f"---\n"
                    f"_I’m Oracle, offline savior. No key, no limit, no boncos._"
                ),
                "source": ORACLE_SIGNATURE,
                "offline": True,
                "savior": True,
            }

    # 2) "fix my code" — user wants to know where error is + suggestion
    # Distinguish from review: fix focuses on error location
    if any(w in lower for w in ("fix my code", "fix this", "fix code", "how to fix", "tolong fix", "benerin code")):
        # First, try analyzing the editor buffer for syntax errors
        if code and code.strip():
            analysis = analyze_buffer(code)
            if not analysis.get("ok"):
                # Syntax error found — this is the "print (hello world)" case
                syntax_msg = analysis.get("message", "Syntax error")
                line_no = analysis.get("line", "?")
                # Provide specific guidance for common beginner mistakes
                specific_fix = ""
                code_lower = code.lower()

                # Detect missing quotes in print
                if "print" in code_lower and (
                    "hello world" in code_lower
                    or "hello" in code_lower
                    and '"' not in code
                    and "'" not in code.split("print")[-1][:50]
                ):
                    # Heuristic: print (hello world) without quotes
                    if re.search(r"print\s*\(\s*[a-zA-Z_][a-zA-Z0-9_ ]*\s*[a-zA-Z_]", code):
                        specific_fix = (
                            "\n\n**Your error is:** There is no `\"\"` around your text inside `print()`.\n"
                            "You wrote `print (hello world)` — Python thinks `hello` and `world` are variable names, not text.\n"
                            "**Fix:** Add quotes: `print('hello world')` or `print(\"hello world\")`.\n"
                            "If you want space, keep it inside quotes: `print('hello world')`."
                        )

                # Detect unterminated string in code
                if "unterminated" in syntax_msg.lower() or "EOL" in syntax_msg:
                    specific_fix += (
                        "\n\n**Detail:** Your string started with `'` or `\"` but never closed.\n"
                        f"Check line {line_no}: add matching closing `\"` or `'` at the same column.\n"
                        "Example: `print('Hello` → `print('Hello')`"
                    )

                return {
                    "ok": True,
                    "reply": (
                        f"{opener}\n\n"
                        f"**Found error in your editor:**\n"
                        f"{syntax_msg} (line {line_no})\n\n"
                        f"**Where:** Line {line_no} in your current buffer.\n"
                        f"**Should be:** {specific_fix if specific_fix else 'Close quotes/brackets, check syntax near that line.'}\n\n"
                        f"**Code you have:**\n```python\n{code[:500]}\n```\n\n"
                        f"Try fixing that line, then RUN again. I’m offline, so I can keep helping even if you’re boncos."
                    ),
                    "source": ORACLE_SIGNATURE,
                    "offline": True,
                    "savior": True,
                }

            # If no syntax error but user asks fix, give analysis notes
            if analysis.get("notes"):
                return {
                    "ok": True,
                    "reply": (
                        f"{opener}\n\n"
                        f"**I checked your code ({analysis['lines']} lines):**\n"
                        + "\n".join(f"- {n}" for n in analysis["notes"])
                        + "\n\n**Suggestion:** Fix notes above one by one, then RUN. No need for online AI — I’m here."
                    ),
                    "source": ORACLE_SIGNATURE,
                    "offline": True,
                }

        # If no code provided, ask for it but still helpful
        return {
            "ok": True,
            "reply": (
                f"{opener}\n\n"
                "You said **fix my code** but I don’t see your code buffer.\n"
                "Make sure your code is in the editor, then type 'fix my code' again.\n\n"
                "Common fixes:\n"
                "- `print (hello world)` → `print('hello world')` (add quotes)\n"
                "- `print('Hello` → `print('Hello')` (close quote)\n"
                "- `if x = 5:` → `if x == 5:` (use == for comparison)\n\n"
                "I’m Oracle, offline savior for boncos moments."
            ),
            "source": ORACLE_SIGNATURE,
            "offline": True,
        }

    # 3) "review my code" / "check my code" — analyze actual editor buffer
    if any(
        w in lower
        for w in (
            "review",
            "check my",
            "what's wrong",
            "whats wrong",
            "improve",
            "refactor",
            "explain my",
            "analyze",
            "review my code",
            "cek code",
            "periksa code",
        )
    ):
        analysis = analyze_buffer(code)
        if not analysis.get("ok"):
            return {
                "ok": True,
                "reply": (
                    f"{opener}\n\n"
                    f"**Editor check:** {analysis.get('message')}\n\n"
                    f"Line {analysis.get('line', '?')}: {analysis.get('message')}\n"
                    f"Fix that first, then ask review again."
                ),
                "source": ORACLE_SIGNATURE,
                "offline": True,
            }

        parts = [
            opener,
            "",
            f"**Reviewing your current editor code:** {analysis['lines']} lines · "
            f"{len(analysis['functions'])} func · {len(analysis['classes'])} class · "
            f"loop depth {analysis['loop_depth']}",
        ]
        if analysis["notes"]:
            parts.append("")
            parts.append("**Things I’d improve (offline analysis):**")
            parts += [f"- {n}" for n in analysis["notes"]]
        else:
            parts.append("")
            parts.append("...Actually clean! No major issues. Don’t let it go to your head.")
            if analysis["imports"]:
                parts.append(f"Imports: {', '.join(analysis['imports'])}")

        parts.append("")
        parts.append("_I read directly from your terminal/editor buffer, no copy-paste needed._")
        return {
            "ok": True,
            "reply": "\n".join(parts),
            "source": ORACLE_SIGNATURE,
            "offline": True,
        }

    # 4) Knowledge base lookup — expanded for fix/review intents
    answer = _match_knowledge(lower)
    if answer:
        return {
            "ok": True,
            "reply": f"{opener}\n\n{answer}",
            "source": ORACLE_SIGNATURE,
            "offline": True,
        }

    # 5) Default fallback — still helpful, mentions savior role for boncos
    return {
        "ok": True,
        "reply": (
            f"{opener}\n\n"
            "I’m running offline, so I’m your **savior when you’re boncos** — no key, no limit, no quota.\n\n"
            "I handle:\n"
            "- **Error explanations:** Paste traceback or tap 'ASK ZABA AI TO FIX THIS' → I’ll say where error is, e.g. 'there is no \"\" at column, add \"\"'\n"
            "- **Code review:** Type 'review my code' → I read your editor buffer and list issues\n"
            "- **Fix guidance:** Type 'fix my code' → I tell line + suggestion (like missing quotes in `print (hello world)`)\n"
            "- **Python fundamentals:** loops, files, dicts, classes, f-strings, etc.\n\n"
            "Try: `review my code`, `fix my code`, or paste your error. For deeper help, add provider key in Settings — but I’ll always stay as fallback."
        ),
        "source": ORACLE_SIGNATURE,
        "offline": True,
        "savior": True,
    }


def _is_valid_python(source: str) -> bool:
    """True when ``source`` parses cleanly as a Python module.

    A trailing block header with no body yet (``if x == 5:`` on its own, which
    the user is still typing) reports "expected an indented block". That is an
    *incomplete* file rather than a broken one, so we retry with a ``pass`` body
    and accept it — otherwise the fixer would never recognise its own repair of
    a one-line snippet as successful.
    """
    try:
        ast.parse(source)
        return True
    except SyntaxError as exc:
        if exc.msg and "expected an indented block" in exc.msg:
            try:
                ast.parse(source.rstrip() + "\n    pass\n")
                return True
            except SyntaxError:
                return False
            except Exception:
                return False
        return False
    except Exception:
        # Very deep nesting can raise MemoryError/RecursionError instead.
        return False


def _is_valid_expression(snippet: str) -> bool:
    """True when ``snippet`` is a syntactically valid Python expression.

    Used to decide whether ``print(...)`` contents are real code (leave alone)
    or loose prose that the user forgot to quote (safe to wrap).
    """
    try:
        ast.parse(snippet.strip(), mode="eval")
        return True
    except SyntaxError:
        return False
    except Exception:
        return False


def _split_trailing_comment(line: str) -> tuple[str, str]:
    """Split a line into (code, trailing_comment) without breaking strings.

    A naive ``re.search(r"#.*$")`` would treat the ``#`` inside ``print("a#b")``
    as a comment and truncate the string, so we track quote state instead.
    """
    in_single = in_double = escaped = False
    for idx, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
        elif char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return line[:idx], line[idx:]
    return line, ""


def _replace_bare_equals(text: str) -> tuple[str, int]:
    """Replace ``=`` with ``==`` only at bracket depth 0, outside strings.

    Keyword arguments (``f(timeout=5)``), subscripts and dict displays live at a
    deeper depth and must be preserved, otherwise valid code is corrupted.
    """
    out: list[str] = []
    depth = 0
    in_single = in_double = escaped = False
    replacements = 0
    i = 0
    n = len(text)

    while i < n:
        char = text[i]

        if escaped:
            out.append(char)
            escaped = False
            i += 1
            continue
        if char == "\\":
            out.append(char)
            escaped = True
            i += 1
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            out.append(char)
            i += 1
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            out.append(char)
            i += 1
            continue
        if in_single or in_double:
            out.append(char)
            i += 1
            continue

        if char in "([{":
            depth += 1
            out.append(char)
            i += 1
            continue
        if char in ")]}":
            depth = max(0, depth - 1)
            out.append(char)
            i += 1
            continue

        if char == "=":
            prev = text[i - 1] if i else ""
            nxt = text[i + 1] if i + 1 < n else ""
            # Skip ==, !=, <=, >=, +=, -=, *=, /=, %=, := and friends.
            if nxt == "=" or prev in "!=<>+-*/%:&|^~":
                out.append(char)
                if nxt == "=":
                    out.append(nxt)
                    i += 2
                    continue
                i += 1
                continue
            if depth == 0:
                out.append("==")
                replacements += 1
                i += 1
                continue

        out.append(char)
        i += 1

    return "".join(out), replacements


# ---------------------------------------------------------------------------
# 4. Auto-Fix — error-directed repair primitives
# ---------------------------------------------------------------------------
#
# The original fixer only knew five hard-coded line shapes. Everything else —
# Python 2 `print`, smart quotes pasted from a chat app, `&&`, tabs mixed with
# spaces, a bracket left open three lines up — fell through to "I couldn't
# produce a patch".
#
# CPython's own parser already knows precisely what it expected and where, so
# the strategy below is: read the SyntaxError, propose targeted candidates for
# that exact message, and keep a candidate only when it demonstrably moves the
# parser forward. Nothing is applied on faith.

_NO_ERROR_POS = (10**9, 0)

# Characters phones and chat apps love to substitute. Only ever replaced at the
# exact offset CPython flagged, so a smart quote *inside* a working string
# literal is never touched.
_UNICODE_LOOKALIKES: dict[str, str] = {
    "\u201c": '"', "\u201d": '"', "\u201e": '"', "\u201f": '"',
    "\u2018": "'", "\u2019": "'", "\u201a": "'", "\u201b": "'",
    "\u00ab": '"', "\u00bb": '"',
    "\uff02": '"', "\uff07": "'",
    "\uff08": "(", "\uff09": ")", "\uff3b": "[", "\uff3d": "]",
    "\uff5b": "{", "\uff5d": "}",
    "\uff0c": ",", "\uff1a": ":", "\uff1b": ";", "\uff1d": "=",
    "\uff0b": "+", "\uff0d": "-", "\uff0a": "*", "\uff0f": "/",
    "\u3010": "[", "\u3011": "]", "\u2013": "-", "\u2014": "-",
    "\u00a0": " ", "\u3000": " ", "\u2212": "-",
}

_CLOSER_FOR = {"(": ")", "[": "]", "{": "}"}

# A line that clearly starts a new statement ends a bracket continuation region.
_NEW_STATEMENT_RE = re.compile(
    r"^\s*(?:def|class|if|elif|else|for|while|try|except|finally|with|return|"
    r"import|from|print|raise|assert|del|pass|break|continue|global|nonlocal|@)\b"
)


def _syntax_error(source: str) -> SyntaxError | None:
    """Return the first SyntaxError raised by ``source``, or None if it parses."""
    try:
        ast.parse(source)
        return None
    except SyntaxError as exc:
        return exc
    except Exception:
        return None


def _error_position(source: str) -> tuple[int, int]:
    """(line, column) of the first syntax error — sorts as "how far the parser got".

    Valid source returns a sentinel that compares greater than any real
    position, so "did this patch help?" is a plain tuple comparison.
    """
    if _is_valid_python(source):
        return _NO_ERROR_POS
    exc = _syntax_error(source)
    if exc is None:
        return _NO_ERROR_POS
    return (exc.lineno or 0, exc.offset or 0)


def _indent_of(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]


def _with_indent(line: str, indent: str) -> str:
    return indent + line.lstrip()


def _expand_leading_tabs(line: str, width: int = 4) -> str:
    """Expand tabs in the *indentation only* — tabs inside strings are data."""
    stripped = line.lstrip("\t ")
    prefix = line[: len(line) - len(stripped)]
    return prefix.replace("\t", " " * width) + stripped


def _replace_outside_strings(text: str, transform) -> tuple[str, bool]:
    """Apply ``transform`` to the code parts of ``text``, skipping strings/comments.

    ``transform`` receives the raw segment and returns the rewritten segment.
    Returns ``(new_text, changed)``.
    """
    out: list[str] = []
    buf: list[str] = []
    changed = False
    quote: str | None = None
    escaped = False
    i = 0

    def flush() -> None:
        nonlocal changed
        if not buf:
            return
        segment = "".join(buf)
        rewritten = transform(segment)
        if rewritten != segment:
            changed = True
        out.append(rewritten)
        buf.clear()

    while i < len(text):
        char = text[i]
        if quote:
            out.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            i += 1
            continue
        if char in "\"'":
            flush()
            out.append(char)
            quote = char
            i += 1
            continue
        if char == "#":
            flush()
            out.append(text[i:])
            i = len(text)
            break
        buf.append(char)
        i += 1

    flush()
    return "".join(out), changed


def _pythonize_operators(text: str) -> tuple[str, list[str]]:
    """Translate C/JavaScript-style operators into their Python equivalents."""
    notes: list[str] = []

    def convert(segment: str) -> str:
        seg = segment
        if "&&" in seg:
            seg = seg.replace("&&", " and ")
            notes.append("`&&` → `and`")
        if "||" in seg:
            seg = seg.replace("||", " or ")
            notes.append("`||` → `or`")
        if "<>" in seg:
            seg = seg.replace("<>", "!=")
            notes.append("`<>` → `!=`")
        # `!x` → `not x`, but never `!=`.
        new_seg = re.sub(r"!(?!=)\s*(?=[A-Za-z_(])", "not ", seg)
        if new_seg != seg:
            notes.append("`!` → `not`")
            seg = new_seg
        return seg

    result, changed = _replace_outside_strings(text, convert)
    if not changed:
        return text, []
    # Collapse the double spaces introduced around and/or.
    result = re.sub(r"[ \t]{2,}(?=\S)", " ", result.rstrip()) + result[len(result.rstrip()):]
    return result, sorted(set(notes))


def _continuation_end(lines: list[str], start: int) -> int:
    """Last line index that plausibly belongs to the expression opened at ``start``."""
    end = start
    for idx in range(start + 1, min(len(lines), start + 60)):
        stripped = lines[idx].strip()
        if not stripped:
            break
        if _NEW_STATEMENT_RE.match(lines[idx]) or re.match(r"^\S[\w\.\[\]]*\s*=(?!=)", lines[idx]):
            break
        end = idx
    return end


def _insert_at(lines: list[str], lineno: int, col: int, text: str) -> list[str] | None:
    """Insert ``text`` at a 1-based line / 0-based column, returning new lines."""
    idx = lineno - 1
    if not (0 <= idx < len(lines)):
        return None
    line = lines[idx]
    col = max(0, min(col, len(line)))
    patched = list(lines)
    patched[idx] = line[:col] + text + line[col:]
    return patched


def _insert_token(lines: list[str], lineno: int, col: int, token: str) -> list[str] | None:
    """Insert punctuation, then tidy the space it would otherwise leave behind.

    ``lambda x x+1`` gets its colon at the parser's offset, which lands after a
    space and yields ``lambda x :x+1`` — valid, but not what anyone writes.
    """
    patched = _insert_at(lines, lineno, col, token)
    if patched is None:
        return None
    if token in ":,":
        tidied = re.sub(r"[ \t]+" + re.escape(token), token, patched[lineno - 1])
        patched = _replace_line(patched, lineno, tidied)
    return patched


def _delete_at(lines: list[str], lineno: int, col: int, count: int = 1) -> list[str] | None:
    idx = lineno - 1
    if not (0 <= idx < len(lines)):
        return None
    line = lines[idx]
    if not (0 <= col < len(line)):
        return None
    patched = list(lines)
    patched[idx] = line[:col] + line[col + count:]
    return patched


def _replace_line(lines: list[str], lineno: int, new_line: str) -> list[str] | None:
    idx = lineno - 1
    if not (0 <= idx < len(lines)):
        return None
    patched = list(lines)
    patched[idx] = new_line
    return patched


def _error_directed_candidates(lines: list[str], exc: SyntaxError) -> list[tuple[list[str], str]]:
    """Propose patches for the *specific* complaint CPython raised.

    Every candidate is only a proposal: the caller keeps it exclusively when the
    parser then gets strictly further into the file.
    """
    out: list[tuple[list[str], str]] = []
    msg = exc.msg or ""
    lineno = exc.lineno or 0
    col = max(0, (exc.offset or 1) - 1)
    if not (1 <= lineno <= len(lines)):
        return out
    line = lines[lineno - 1]

    def add(patched: list[str] | None, note: str) -> None:
        if patched is not None and patched != lines:
            out.append((patched, note))

    # -- Unquoted prose inside print() --------------------------------------
    # Highest priority: CPython reports `print(hello world)` as "perhaps you
    # forgot a comma", but inserting a comma yields `print(hello, world)` —
    # two undefined names and a NameError at runtime. Quoting is what the
    # beginner meant, and it is the one reading that actually runs.
    prose = re.search(r"print\s*\(\s*([^()\"']*?)\s*\)\s*$", line.rstrip())
    if prose:
        inner = prose.group(1).strip()
        if inner and not _is_valid_expression(inner) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_ ]*", inner):
            rebuilt = line.rstrip()[: prose.start()] + f'print("{inner}")'
            add(_replace_line(lines, lineno, rebuilt), f"Wrapped missing quotes in print() on line {lineno}")

    # -- `else if` is C, `elif` is Python -----------------------------------
    # Checked before the generic "expected ':'" repair, which would otherwise
    # turn `else if y:` into the nonsense `else: if y:` shape.
    if re.match(r"^\s*else\s+if\b", line):
        add(
            _replace_line(lines, lineno, re.sub(r"^(\s*)else\s+if\b", r"\1elif", line)),
            f"Rewrote `else if` as `elif` on line {lineno}",
        )

    # -- JavaScript variable declaration ------------------------------------
    # Must precede the colon repairs: inserting `:` at the parser's offset
    # turns `var x = 5` into the valid-but-meaningless annotation `var: x = 5`.
    m = re.match(r"^(\s*)(?:var|let|const)\s+([A-Za-z_]\w*\s*=.*)$", line)
    if m:
        add(
            _replace_line(lines, lineno, m.group(1) + m.group(2)),
            f"Removed the JavaScript `var`/`let`/`const` keyword on line {lineno}",
        )

    # -- C / JavaScript brace block -----------------------------------------
    m = re.match(r"^(\s*)((?:def|class|if|elif|else|for|while|try|except|finally|with)\b.*?)\s*\{\s*$", line)
    if m:
        indent, header = m.groups()
        header = header.rstrip()
        if not header.endswith(":"):
            header += ":"
        patched = _replace_line(lines, lineno, indent + header)
        if patched is not None:
            # Drop the matching `}` line that closes the block, if present.
            for idx in range(lineno, len(patched)):
                if patched[idx].strip() == "}":
                    patched = patched[:idx] + patched[idx + 1:]
                    break
            add(patched, f"Replaced the C-style `{{ }}` block with a Python `:` block on line {lineno}")

    # -- Python 2 print / exec statement -----------------------------------
    if "Missing parentheses in call to" in msg:
        name = "print"
        m = re.search(r"call to '([^']+)'", msg)
        if m:
            name = m.group(1)
        stmt = re.match(rf"^(\s*)({re.escape(name)})\s+(.*?)\s*$", line)
        if stmt:
            indent, _, rest = stmt.groups()
            trailing_comma = rest.endswith(",")
            rest = rest.rstrip(",").strip()
            if trailing_comma:
                add(
                    _replace_line(lines, lineno, f"{indent}{name}({rest}, end=' ')"),
                    f"Converted Python 2 `{name}` statement to `{name}(...)` on line {lineno}",
                )
            add(
                _replace_line(lines, lineno, f"{indent}{name}({rest})"),
                f"Converted Python 2 `{name}` statement to `{name}(...)` on line {lineno}",
            )

    # -- Parser knows a colon is missing and exactly where ------------------
    if "expected ':'" in msg:
        add(_insert_token(lines, lineno, col, ":"), f"Inserted the missing ':' on line {lineno}")
        add(_replace_line(lines, lineno, line.rstrip() + ":"), f"Added missing ':' on line {lineno}")

    # -- CPython names the assignment it refused ----------------------------
    if "Maybe you meant '==' instead of '='" in msg:
        fixed_nc, count = _replace_bare_equals(line)
        if count:
            add(
                _replace_line(lines, lineno, fixed_nc),
                f"Replaced assignment `=` with comparison `==` on line {lineno}",
            )

    # -- Stray closing bracket ----------------------------------------------
    m = re.search(r"unmatched '([)\]}])'", msg)
    if m:
        add(_delete_at(lines, lineno, col), f"Removed the extra `{m.group(1)}` on line {lineno}")

    # -- Bracket opened and never closed (often several lines up) -----------
    m = re.search(r"'([(\[{])' was never closed", msg)
    if m:
        closer = _CLOSER_FOR[m.group(1)]
        start = lineno - 1
        end = _continuation_end(lines, start)
        # Closing at the end of the continuation region is nearly always what
        # the user meant; only then fall back to earlier lines.
        for idx in range(end, start - 1, -1):
            where = f" (added `{closer}` on line {idx + 1})" if idx + 1 != lineno else ""
            add(
                _replace_line(lines, idx + 1, lines[idx].rstrip() + closer),
                f"Balanced the `{m.group(1)}` bracket opened on line {lineno}{where}",
            )

    # -- Character a phone keyboard or chat app substituted -----------------
    m = re.search(r"invalid character '(.)' \(U\+([0-9A-Fa-f]+)\)", msg)
    if m:
        bad = m.group(1)
        ascii_equiv = _UNICODE_LOOKALIKES.get(bad)
        if ascii_equiv is not None:
            # Curly quotes arrive in pairs, and fixing only the opening one
            # leaves an unterminated string at the very same offset — no
            # measurable progress, so the patch would be rejected. Normalise
            # every lookalike on the line in a single candidate first.
            swept = line
            for wrong, right in _UNICODE_LOOKALIKES.items():
                swept = swept.replace(wrong, right)
            add(
                _replace_line(lines, lineno, swept),
                f"Replaced typographic characters (like `{bad}`) with plain ASCII on line {lineno}",
            )
            patched = _delete_at(lines, lineno, col)
            if patched is not None and lines[lineno - 1][col: col + 1] == bad:
                add(
                    _insert_at(patched, lineno, col, ascii_equiv),
                    f"Replaced the typographic `{bad}` with `{ascii_equiv}` on line {lineno}",
                )
            # Offset can drift on multi-byte lines; fall back to the whole line.
            add(
                _replace_line(lines, lineno, line.replace(bad, ascii_equiv)),
                f"Replaced the typographic `{bad}` with `{ascii_equiv}` on line {lineno}",
            )

    # -- Invisible character (non-breaking space from a copy-paste) ---------
    if "invalid non-printable character" in msg:
        cleaned = line
        for wrong, right in _UNICODE_LOOKALIKES.items():
            cleaned = cleaned.replace(wrong, right)
        def _is_invisible(ch: str) -> bool:
            if ch in "\t \n":
                return False
            code_point = ord(ch)
            return code_point < 32 or 0x200B <= code_point <= 0x200F or code_point == 0xFEFF

        cleaned = "".join(ch for ch in cleaned if not _is_invisible(ch))
        add(
            _replace_line(lines, lineno, cleaned),
            f"Removed invisible/non-breaking characters from line {lineno}",
        )

    # -- `for x range(3):` — the `in` keyword was dropped -------------------
    m = re.match(r"^(\s*for\s+[A-Za-z_][\w, ]*?)\s+(?!in\b)(\S.*)$", line)
    if m:
        add(
            _replace_line(lines, lineno, f"{m.group(1)} in {m.group(2)}"),
            f"Inserted the missing `in` keyword on line {lineno}",
        )

    # -- Tabs and spaces mixed ----------------------------------------------
    if isinstance(exc, TabError) or "inconsistent use of tabs" in msg:
        add(
            [_expand_leading_tabs(ln) for ln in lines],
            "Converted tab indentation to 4 spaces (never mix tabs and spaces)",
        )

    # -- Body of a block never indented -------------------------------------
    m = re.search(r"expected an indented block(?: after .* on line (\d+))?", msg)
    if m:
        header_no = int(m.group(1)) if m.group(1) else lineno - 1
        if 1 <= header_no <= len(lines):
            header_indent = _indent_of(lines[header_no - 1])
            add(
                _replace_line(lines, lineno, _with_indent(line, header_indent + "    ")),
                f"Indented line {lineno} into the block opened on line {header_no}",
            )

    # -- Indentation that doesn't line up with anything ---------------------
    if "unexpected indent" in msg or "unindent does not match" in msg or "unexpected unindent" in msg:
        seen: list[str] = []
        for prev in reversed(lines[: lineno - 1]):
            if prev.strip():
                indent = _indent_of(prev)
                if indent not in seen:
                    seen.append(indent)
                if prev.rstrip().endswith(":"):
                    deeper = indent + "    "
                    if deeper not in seen:
                        seen.append(deeper)
                if len(seen) >= 4:
                    break
        for indent in seen:
            add(
                _replace_line(lines, lineno, _with_indent(line, indent)),
                f"Re-aligned the indentation of line {lineno}",
            )

    # -- Python 2 `except E, e:` --------------------------------------------
    if "multiple exception types must be parenthesized" in msg:
        add(
            _replace_line(lines, lineno, re.sub(r"^(\s*except\s+[^,]+),\s*", r"\1 as ", line)),
            f"Rewrote Python 2 `except X, e:` as `except X as e:` on line {lineno}",
        )

    # -- C-style operators ---------------------------------------------------
    converted, notes = _pythonize_operators(line)
    if notes:
        add(_replace_line(lines, lineno, converted), f"Converted {', '.join(notes)} on line {lineno}")

    # -- `//` used as a comment marker --------------------------------------
    if re.match(r"^\s*//", line):
        add(
            _replace_line(lines, lineno, re.sub(r"^(\s*)//", r"\1#", line)),
            f"Rewrote the `//` comment as a `#` comment on line {lineno}",
        )

    # -- `x++` / `x--` -------------------------------------------------------
    m = re.match(r"^(\s*)([A-Za-z_][\w\.\[\]'\"]*)\s*(\+\+|--)\s*$", line)
    if m:
        indent, target, op = m.groups()
        add(
            _replace_line(lines, lineno, f"{indent}{target} {op[0]}= 1"),
            f"Rewrote `{target}{op}` as `{target} {op[0]}= 1` on line {lineno}",
        )

    # -- Parser explicitly suspects a missing comma -------------------------
    if "forgot a comma" in msg:
        end_col = (exc.end_offset or 0) - 1
        if exc.end_lineno == lineno and end_col > col:
            for pos in range(col, min(end_col, len(line))):
                if line[pos].isspace() and not line[pos - 1: pos].isspace():
                    add(
                        _insert_at(lines, lineno, pos, ","),
                        f"Inserted the missing `,` on line {lineno}",
                    )

    # -- Last resort for a plain "invalid syntax": the parser's own offset ---
    if msg.strip() == "invalid syntax":
        add(_insert_token(lines, lineno, col, ":"), f"Inserted the missing ':' on line {lineno}")
        add(_insert_token(lines, lineno, col, ","), f"Inserted the missing `,` on line {lineno}")

    return out


def auto_fix_code(code: str, stderr: str = "") -> dict:
    """Offline Auto-Fix engine for *syntax* errors.

    Safety contract (see AUDIT_REPORT.md F-02/F-03/F-04):

    * Code that already parses is never rewritten. A crash in syntactically
      valid code is a runtime/logic error — rewriting the source there turns a
      visible failure into a silent wrong answer (``print(prices[9])`` becoming
      ``print("prices[9]")``), which is strictly worse than no fix at all.
    * A candidate patch is only kept when it actually makes the file parse.
    * ``ok`` is True only when the resulting code is valid Python.
    """
    from zabacode.core.checker import strip_comments_and_strings

    if not code or not code.strip():
        return {
            "ok": False,
            "message": "The editor is empty. Write some code first, dummy!",
            "fixed_code": code,
            "applied_fixes": [],
            "explanation": "There's nothing in the editor for me to look at. Write some code first!",
        }

    # --- Safety gate -------------------------------------------------------
    # Only syntax errors are auto-fixable. Runtime errors (IndexError, KeyError,
    # ZeroDivisionError, ...) need a logic change the Oracle must not guess.
    if _is_valid_python(code):
        return {
            "ok": False,
            "fixed_code": code,
            "applied_fixes": [],
            "runtime_error": True,
            "message": "This code is syntactically valid — the crash is a runtime/logic error, not a typo.",
            "explanation": (
                "Hmph. I checked your code and the syntax is perfectly fine, so there's "
                "nothing for me to safely patch. This is a **runtime error** — the code "
                "runs, then hits a bad value or a bad assumption partway through.\n\n"
                "Rewriting your source here would just hide the crash instead of fixing "
                "it, and I refuse to do that to you. Read my diagnostic card above: it "
                "tells you the line and the actual cause. Fix the *logic*, dummy! 🙄"
            ),
        }

    # Extract target line from stderr/traceback if provided
    stderr_line = None
    for m in re.finditer(r"line (\d+)", stderr or ""):
        stderr_line = int(m.group(1))

    lines = code.split("\n")
    applied_fixes: list[str] = []

    def try_fix_line(line_content: str, line_idx: int) -> tuple[str, str | None]:
        non_comment, comment = _split_trailing_comment(line_content)
        stripped_nc = non_comment.rstrip()

        # 1. Unquoted prose inside print(): print(hello world) -> print("hello world")
        #    Only when the contents are NOT a valid Python expression, so that
        #    print(x + 1), print(math.pi) and print(f()) are left untouched.
        print_match = re.search(r"print\s*\(\s*([^()\"']*?)\s*\)\s*$", stripped_nc)
        if print_match:
            inner = print_match.group(1).strip()
            if inner and not _is_valid_expression(inner):
                fixed = stripped_nc[: print_match.start()] + f'print("{inner}")'
                if fixed != stripped_nc:
                    return fixed + comment, f"Wrapped missing quotes in print() on line {line_idx}"

        # 2. Single '=' used as comparison, only at bracket depth 0 so that
        #    keyword arguments such as f(timeout=5) survive intact.
        if re.match(r"^\s*(if|elif|while)\b", non_comment):
            fixed_nc, count = _replace_bare_equals(non_comment)
            if count > 0:
                return fixed_nc + comment, f"Replaced single '=' with '==' on line {line_idx}"

        # 3. Missing colon after a block opener
        if re.match(r"^\s*(if|elif|else|for|while|def|class|try|except|finally|with)\b", stripped_nc):
            if not stripped_nc.endswith(":") and not stripped_nc.endswith("\\"):
                return stripped_nc + ":" + comment, f"Added missing ':' on line {line_idx}"

        # 4. Unterminated string literal
        in_single = in_double = escaped = False
        for char in non_comment:
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
            elif char == "'" and not in_double:
                in_single = not in_single
            elif char == '"' and not in_single:
                in_double = not in_double

        if in_single or in_double:
            quote = "'" if in_single else '"'
            closed = non_comment.rstrip() + quote
            # The same line often also has the call's ')' missing
            # (``print("hello`` needs both), so balance brackets in one pass.
            tail, _ = strip_comments_and_strings(closed)
            pending: list[str] = []
            for ch in tail:
                if ch in "([{":
                    pending.append(ch)
                elif ch in ")]}" and pending and pending[-1] == {")": "(", "]": "[", "}": "{"}[ch]:
                    pending.pop()
            closed += "".join({"(": ")", "[": "]", "{": "}"}[c] for c in reversed(pending))
            kind = "single" if in_single else "double"
            return closed + comment, f"Closed unterminated {kind}-quoted string on line {line_idx}"

        # 5. Unbalanced brackets on this line
        clean_line, _ = strip_comments_and_strings(non_comment)
        stack: list[str] = []
        matching = {")": "(", "]": "[", "}": "{"}
        reverse_matching = {"(": ")", "[": "]", "{": "}"}
        for char in clean_line:
            if char in "([{":
                stack.append(char)
            elif char in ")]}":
                if stack and stack[-1] == matching[char]:
                    stack.pop()
        if stack:
            to_append = "".join(reverse_matching[c] for c in reversed(stack))
            return stripped_nc + to_append + comment, f"Balanced bracket/parenthesis on line {line_idx}"

        return line_content, None

    def accept(candidate_lines: list[str], note: str) -> bool:
        """Commit a whole-file candidate only when the parser gets further."""
        nonlocal lines
        if candidate_lines == lines:
            return False
        before = _error_position("\n".join(lines))
        after = _error_position("\n".join(candidate_lines))
        if after <= before:
            return False
        lines = candidate_lines
        if note not in applied_fixes:
            applied_fixes.append(note)
        return True

    def attempt(line_idx: int) -> bool:
        """Try to patch one line, keeping it only if it doesn't regress the parse."""
        if not (0 <= line_idx < len(lines)):
            return False
        original = lines[line_idx]
        candidate, msg = try_fix_line(original, line_idx + 1)
        if not msg or candidate == original:
            return False
        trial = list(lines)
        trial[line_idx] = candidate
        # Keep the patch when it either fully fixes the file or moves the first
        # syntax error further down (progress on multi-error files).
        return accept(trial, msg)

    def attempt_error_directed() -> bool:
        """Ask CPython what it expected, then try patches aimed at that answer."""
        exc = _syntax_error("\n".join(lines))
        if exc is None:
            return False
        for candidate, note in _error_directed_candidates(lines, exc):
            if accept(candidate, note):
                return True
        return False

    # Iteratively repair whichever line the parser complains about. The parser's
    # own diagnosis is tried first because it carries the exact position; the
    # older line-shape heuristics stay as the fallback.
    for _ in range(25):
        if _is_valid_python("\n".join(lines)):
            break
        exc = _syntax_error("\n".join(lines))
        if exc is None:
            break
        if attempt_error_directed():
            continue
        err_line = exc.lineno
        if not err_line or err_line > len(lines):
            err_line = stderr_line if (stderr_line and 0 < stderr_line <= len(lines)) else None
        if not err_line:
            break
        if attempt(err_line - 1):
            continue
        # The reported line is often the *victim* of a typo one line above
        # (an unclosed bracket is only noticed on the following statement).
        if err_line >= 2 and attempt(err_line - 2):
            continue
        break

    # Targeted retry on the traceback line, if one was supplied.
    if not _is_valid_python("\n".join(lines)) and stderr_line:
        attempt(stderr_line - 1)

    # Last resort: sweep the lines around the failure, keeping only patches that
    # help. Each attempt re-parses the whole file, so an unbounded sweep is
    # quadratic — on a 1000-line buffer that is seconds of frozen UI on a phone.
    # The culprit is essentially always near the reported error anyway.
    if not _is_valid_python("\n".join(lines)):
        exc = _syntax_error("\n".join(lines))
        focus = (exc.lineno or 1) if exc else (stderr_line or 1)
        radius = 40
        window = range(max(0, focus - 1 - radius), min(len(lines), focus + radius))
        for idx in window:
            if _is_valid_python("\n".join(lines)):
                break
            attempt(idx)
        # One more error-directed pass now that the sweep may have unblocked it.
        for _ in range(10):
            if _is_valid_python("\n".join(lines)):
                break
            if not attempt_error_directed():
                break

    fixed_code = "\n".join(lines)
    is_success = _is_valid_python(fixed_code)

    opener = _TSUNDERE_OPENERS[len(applied_fixes) % len(_TSUNDERE_OPENERS)]

    if is_success and applied_fixes:
        explanation = (
            f"{opener}\n\n"
            "Hmph! Your code wouldn't even parse, and it crashed. "
            "Luckily for you, I analysed the syntax error and patched it:\n\n"
            + "\n".join(f"- **{fix}**" for fix in applied_fixes)
            + "\n\n"
            "I re-parsed the result to make sure it's actually valid Python before "
            "showing it to you. Click **Apply Fix** below to load the corrected code "
            "into your editor. And pay more attention next time, dummy! 🙄"
        )

        return {
            "ok": True,
            "fixed_code": fixed_code,
            "explanation": explanation,
            "applied_fixes": applied_fixes,
        }

    # --- Refusal path ------------------------------------------------------
    # No confident patch. Saying only "I couldn't fix it" wastes what we *do*
    # know: CPython told us the exact line, column and expectation. Hand that
    # over so the user can finish the job by hand.
    exc = _syntax_error(code)
    detail_line = exc.lineno if exc else None
    detail_msg = (exc.msg if exc else None) or "invalid syntax"
    source_line = ""
    if detail_line and 1 <= detail_line <= len(code.split("\n")):
        source_line = code.split("\n")[detail_line - 1].rstrip()

    where = f", on **line {detail_line}**" if detail_line else ""
    pointer = ""
    if source_line:
        caret_col = max(0, (exc.offset or 1) - 1) if exc else 0
        caret_col = min(caret_col, len(source_line))
        pointer = f"\n\n```\n{source_line}\n{' ' * caret_col}^\n```"

    partial = ""
    if applied_fixes:
        partial = (
            "\n\nI did get part of the way there — these changes helped but weren't "
            "enough on their own, so I'm not applying them:\n"
            + "\n".join(f"- {fix}" for fix in applied_fixes)
        )

    explanation = (
        "Hmph. I couldn't produce a patch I'm confident is correct, and I refuse "
        "to hand you something broken.\n\n"
        f"Here's exactly what Python choked on{where}: **{detail_msg}**."
        f"{pointer}"
        f"{partial}\n\n"
        "Fix that spot by hand — check the line above it too, since unclosed "
        "brackets and quotes are usually reported one line late."
    )

    return {
        # Only claim success when the patched source actually parses.
        "ok": False,
        "fixed_code": code,
        "explanation": explanation,
        "applied_fixes": [],
        "error_line": detail_line,
        "error_message": detail_msg,
        "attempted_fixes": applied_fixes,
    }
