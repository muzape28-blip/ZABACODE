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
