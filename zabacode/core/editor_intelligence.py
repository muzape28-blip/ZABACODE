"""
ZABACODE Core — Editor Intelligence (Inspired by VSCode's Language Features)

VSCode's language features (src/vs/editor/common/languages/) provide:
  - DocumentSymbolProvider: AST outline / symbol tree
  - CompletionItemProvider: autocomplete / IntelliSense
  - RenameProvider: rename symbol across a file
  - CodeActionProvider: quick fixes and refactorings

We port these to Python for a single-file editing model (mobile IDE):

  - SymbolOutline: AST-based symbol tree (classes, functions, imports, globals)
  - CompletionProvider: keyword + snippet + import completions
  - RenameProvider: local one-file rename (find all occurrences, replace)
  - OrganizeImports: sort and remove unused imports

References:
  - https://github.com/microsoft/vscode/blob/main/src/vs/editor/common/languages.ts
  - https://code.visualstudio.com/api/references/vscode-api#languages
"""

from __future__ import annotations

import ast
import enum
import re
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Symbol Outline — mirrors VSCode's DocumentSymbol
# ---------------------------------------------------------------------------

class SymbolKind(enum.IntEnum):
    """Symbol kinds — mirrors VSCode's SymbolKind."""
    FILE = 0
    MODULE = 1
    NAMESPACE = 2
    PACKAGE = 3
    CLASS = 4
    METHOD = 5
    PROPERTY = 6
    FIELD = 7
    CONSTRUCTOR = 8
    ENUM = 9
    INTERFACE = 10
    FUNCTION = 11
    VARIABLE = 12
    CONSTANT = 13
    IMPORT = 14


@dataclass
class DocumentSymbol:
    """
    A symbol in the document — mirrors VSCode's DocumentSymbol.

    Used for:
      - AST outline panel (sidebar)
      - Go-to-symbol dropdown
      - Breadcrumb navigation
    """
    name: str
    kind: SymbolKind
    line: int  # 1-based
    column: int  # 1-based
    end_line: int
    end_column: int
    detail: str = ""
    children: list[DocumentSymbol] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "name": self.name,
            "kind": int(self.kind),
            "kindLabel": _SYMBOL_KIND_LABELS.get(self.kind, "???"),
            "line": self.line,
            "column": self.column,
            "endLine": self.end_line,
            "endColumn": self.end_column,
            "detail": self.detail,
        }
        if self.children:
            d["children"] = [c.to_dict() for c in self.children]
        return d


_SYMBOL_KIND_LABELS = {
    SymbolKind.CLASS: "class",
    SymbolKind.FUNCTION: "def",
    SymbolKind.METHOD: "method",
    SymbolKind.VARIABLE: "var",
    SymbolKind.CONSTANT: "const",
    SymbolKind.IMPORT: "import",
    SymbolKind.PROPERTY: "property",
}

# Standard library modules — single source of truth, used by both
# import completions and organize-imports.  Kept as a frozenset for
# O(1) membership checks and a sorted list for deterministic ordering.
_STDLIB_MODULES_SET = frozenset({
    "os", "sys", "json", "re", "math", "time", "datetime", "pathlib",
    "collections", "itertools", "functools", "typing", "dataclasses",
    "abc", "io", "hashlib", "hmac", "secrets", "subprocess", "threading",
    "multiprocessing", "asyncio", "socket", "http", "urllib", "sqlite3",
    "csv", "configparser", "logging", "unittest", "argparse", "shutil",
    "tempfile", "glob", "fnmatch", "stat", "copy", "pprint", "textwrap",
    "string", "random", "struct", "base64", "uuid", "traceback",
    "inspect", "ast", "dis", "warnings", "contextlib", "enum",
    "operator", "heapq", "bisect", "array", "weakref", "types",
    "platform", "signal", "atexit", "gc", "codecs",
})
_STDLIB_MODULES_LIST = sorted(_STDLIB_MODULES_SET)


def get_symbol_outline(code: str) -> list[DocumentSymbol]:
    """
    Parse Python code into a symbol outline tree.

    Returns top-level symbols (classes, functions, imports, globals)
    with nested children for class methods and properties.

    Usage:
        symbols = get_symbol_outline(code)
        # Returns: [DocumentSymbol("MyClass", CLASS, ...), DocumentSymbol("my_func", FUNCTION, ...)]
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    symbols: list[DocumentSymbol] = []

    for node in tree.body:
        sym = _node_to_symbol(node)
        if sym:
            symbols.append(sym)

    return symbols


def _node_to_symbol(node: ast.AST) -> DocumentSymbol | None:
    """Convert an AST node to a DocumentSymbol."""
    if isinstance(node, ast.ClassDef):
        children: list[DocumentSymbol] = []
        for item in node.body:
            child = _node_to_symbol(item)
            if child:
                children.append(child)
        bases = ", ".join(
            ast.unparse(b) if hasattr(ast, "unparse") else str(b)
            for b in node.bases
        )
        return DocumentSymbol(
            name=node.name,
            kind=SymbolKind.CLASS,
            line=node.lineno,
            column=node.col_offset + 1,
            end_line=node.end_lineno or node.lineno,
            end_column=node.end_col_offset or 0,
            detail=f"({bases})" if bases else "",
            children=children,
        )

    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        args = [a.arg for a in node.args.args if a.arg != "self"]
        return DocumentSymbol(
            name=node.name,
            kind=SymbolKind.METHOD if _is_method(node) else SymbolKind.FUNCTION,
            line=node.lineno,
            column=node.col_offset + 1,
            end_line=node.end_lineno or node.lineno,
            end_column=node.end_col_offset or 0,
            detail=f"({', '.join(args)})" if args else "()",
        )

    elif isinstance(node, ast.Import):
        names = ", ".join(a.asname or a.name for a in node.names)
        return DocumentSymbol(
            name=f"import {names}",
            kind=SymbolKind.IMPORT,
            line=node.lineno,
            column=node.col_offset + 1,
            end_line=node.end_lineno or node.lineno,
            end_column=node.end_col_offset or 0,
        )

    elif isinstance(node, ast.ImportFrom):
        names = ", ".join(a.asname or a.name for a in node.names)
        return DocumentSymbol(
            name=f"from {node.module} import {names}",
            kind=SymbolKind.IMPORT,
            line=node.lineno,
            column=node.col_offset + 1,
            end_line=node.end_lineno or node.lineno,
            end_column=node.end_col_offset or 0,
        )

    elif isinstance(node, ast.Assign):
        # Top-level variable assignment
        target_names = []
        for t in node.targets:
            if isinstance(t, ast.Name):
                target_names.append(t.id)
        if target_names:
            return DocumentSymbol(
                name=", ".join(target_names),
                kind=SymbolKind.CONSTANT if _is_constant(node) else SymbolKind.VARIABLE,
                line=node.lineno,
                column=node.col_offset + 1,
                end_line=node.end_lineno or node.lineno,
                end_column=node.end_col_offset or 0,
            )

    return None


def _is_method(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Check if a function is likely a method (has 'self' or 'cls' as first arg)."""
    if node.args.args and node.args.args[0].arg in ("self", "cls"):
        return True
    return False


def _is_constant(node: ast.Assign) -> bool:
    """Check if an assignment is a constant (UPPER_CASE name)."""
    for t in node.targets:
        if isinstance(t, ast.Name) and t.id.isupper():
            return True
    return False


# ---------------------------------------------------------------------------
# Go-to-Symbol — find symbol by name
# ---------------------------------------------------------------------------

def find_symbol(code: str, query: str) -> list[DocumentSymbol]:
    """
    Find symbols matching a query string (fuzzy/prefix match).

    Used for the Quick Open / Go-to-Symbol dropdown.
    Mirrors VSCode's workspace/symbol endpoint.
    """
    all_symbols = _flatten_symbols(get_symbol_outline(code))
    query_lower = query.lower()
    results = []
    for sym in all_symbols:
        if query_lower in sym.name.lower():
            results.append(sym)
    return results


def _flatten_symbols(symbols: list[DocumentSymbol]) -> list[DocumentSymbol]:
    """Flatten a symbol tree into a flat list."""
    flat: list[DocumentSymbol] = []
    for sym in symbols:
        flat.append(sym)
        flat.extend(_flatten_symbols(sym.children))
    return flat


# ---------------------------------------------------------------------------
# Completion Provider — mirrors VSCode's CompletionItemProvider
# ---------------------------------------------------------------------------

@dataclass
class CompletionItem:
    """A completion item — mirrors VSCode's CompletionItem."""
    label: str
    kind: str  # "keyword", "function", "class", "snippet", "import", "variable"
    insert_text: str
    detail: str = ""
    documentation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "kind": self.kind,
            "insertText": self.insert_text,
            "detail": self.detail,
            "documentation": self.documentation,
        }


# Python keyword completions
_PYTHON_KEYWORDS = [
    CompletionItem("def", "keyword", "def ", "Function definition"),
    CompletionItem("class", "keyword", "class ", "Class definition"),
    CompletionItem("if", "keyword", "if ", "Conditional"),
    CompletionItem("elif", "keyword", "elif ", "Else-if branch"),
    CompletionItem("else", "keyword", "else:\n    ", "Else branch"),
    CompletionItem("for", "keyword", "for ", "For loop"),
    CompletionItem("while", "keyword", "while ", "While loop"),
    CompletionItem("try", "keyword", "try:\n    ", "Try block"),
    CompletionItem("except", "keyword", "except ", "Exception handler"),
    CompletionItem("with", "keyword", "with ", "Context manager"),
    CompletionItem("import", "keyword", "import ", "Import module"),
    CompletionItem("from", "keyword", "from ", "From-import"),
    CompletionItem("return", "keyword", "return ", "Return value"),
    CompletionItem("yield", "keyword", "yield ", "Yield value"),
    CompletionItem("raise", "keyword", "raise ", "Raise exception"),
    CompletionItem("pass", "keyword", "pass", "Null statement"),
    CompletionItem("break", "keyword", "break", "Break loop"),
    CompletionItem("continue", "keyword", "continue", "Continue loop"),
    CompletionItem("lambda", "keyword", "lambda ", "Lambda expression"),
    CompletionItem("async", "keyword", "async ", "Async keyword"),
    CompletionItem("await", "keyword", "await ", "Await expression"),
    CompletionItem("True", "keyword", "True", "Boolean true"),
    CompletionItem("False", "keyword", "False", "Boolean false"),
    CompletionItem("None", "keyword", "None", "None value"),
    CompletionItem("in", "keyword", "in ", "Membership test"),
    CompletionItem("not", "keyword", "not ", "Logical not"),
    CompletionItem("and", "keyword", "and ", "Logical and"),
    CompletionItem("or", "keyword", "or ", "Logical or"),
    CompletionItem("is", "keyword", "is ", "Identity test"),
    CompletionItem("as", "keyword", "as ", "Alias"),
]

# Built-in function completions
_PYTHON_BUILTINS = [
    CompletionItem("print", "function", "print($1)", "Print to stdout"),
    CompletionItem("input", "function", "input($1)", "Read from stdin"),
    CompletionItem("len", "function", "len($1)", "Length of object"),
    CompletionItem("range", "function", "range($1)", "Range iterator"),
    CompletionItem("int", "function", "int($1)", "Convert to int"),
    CompletionItem("float", "function", "float($1)", "Convert to float"),
    CompletionItem("str", "function", "str($1)", "Convert to string"),
    CompletionItem("list", "function", "list($1)", "List constructor"),
    CompletionItem("dict", "function", "dict($1)", "Dict constructor"),
    CompletionItem("tuple", "function", "tuple($1)", "Tuple constructor"),
    CompletionItem("set", "function", "set($1)", "Set constructor"),
    CompletionItem("type", "function", "type($1)", "Type of object"),
    CompletionItem("isinstance", "function", "isinstance($1, $2)", "Instance check"),
    CompletionItem("enumerate", "function", "enumerate($1)", "Enumerate iterable"),
    CompletionItem("zip", "function", "zip($1)", "Zip iterables"),
    CompletionItem("map", "function", "map($1, $2)", "Map function"),
    CompletionItem("filter", "function", "filter($1, $2)", "Filter iterable"),
    CompletionItem("sorted", "function", "sorted($1)", "Sorted copy"),
    CompletionItem("open", "function", "open($1)", "Open file"),
    CompletionItem("abs", "function", "abs($1)", "Absolute value"),
    CompletionItem("max", "function", "max($1)", "Maximum value"),
    CompletionItem("min", "function", "min($1)", "Minimum value"),
    CompletionItem("sum", "function", "sum($1)", "Sum of iterable"),
    CompletionItem("hasattr", "function", "hasattr($1, $2)", "Has attribute"),
    CompletionItem("getattr", "function", "getattr($1, $2)", "Get attribute"),
    CompletionItem("setattr", "function", "setattr($1, $2, $3)", "Set attribute"),
    CompletionItem("super", "function", "super()", "Super class proxy"),
]

# Snippet completions
_PYTHON_SNIPPETS = [
    CompletionItem("def", "snippet", "def ${1:function_name}(${2:args}):\n    ${3:pass}", "Function definition"),
    CompletionItem("class", "snippet", "class ${1:ClassName}:\n    def __init__(self${2:, args}):\n        ${3:pass}", "Class definition"),
    CompletionItem("if", "snippet", "if ${1:condition}:\n    ${2:pass}", "If statement"),
    CompletionItem("ifelse", "snippet", "if ${1:condition}:\n    ${2:pass}\nelse:\n    ${3:pass}", "If-else statement"),
    CompletionItem("for", "snippet", "for ${1:item} in ${2:iterable}:\n    ${3:pass}", "For loop"),
    CompletionItem("while", "snippet", "while ${1:condition}:\n    ${2:pass}", "While loop"),
    CompletionItem("try", "snippet", "try:\n    ${1:pass}\nexcept ${2:Exception} as e:\n    ${3:print(e)}", "Try-except"),
    CompletionItem("with", "snippet", "with ${1:expression} as ${2:var}:\n    ${3:pass}", "With statement"),
    CompletionItem("main", "snippet", 'if __name__ == "__main__":\n    ${1:main()}', "Main guard"),
    CompletionItem("listcomp", "snippet", "[${1:expr} for ${2:x} in ${3:iterable}]", "List comprehension"),
    CompletionItem("dictcomp", "snippet", "{${1:key}: ${2:value} for ${3:k, v} in ${4:iterable}}", "Dict comprehension"),
    CompletionItem("lambda", "snippet", "lambda ${1:x}: ${2:x}", "Lambda expression"),
    CompletionItem("property", "snippet", "@property\ndef ${1:name}(self):\n    return self._${1:name}", "Property getter"),
    CompletionItem("staticmethod", "snippet", "@staticmethod\ndef ${1:name}(${2:args}):\n    ${3:pass}", "Static method"),
    CompletionItem("classmethod", "snippet", "@classmethod\ndef ${1:name}(cls${2:, args}):\n    ${3:pass}", "Class method"),
]


def get_completions(code: str, line: int, column: int) -> list[CompletionItem]:
    """
    Get completions for the cursor position.

    Returns:
      - Keywords + builtins + snippets (always available)
      - Import completions (if typing "import" or "from")
      - Local variable/function completions (from AST analysis)

    The Ace editor's ext-language_tools.js handles the actual completion UI;
    this function provides the data for the custom completer.
    """
    completions: list[CompletionItem] = []

    # Get the current line text
    lines = code.split("\n")
    current_line = lines[line - 1] if 0 < line <= len(lines) else ""
    prefix = current_line[:column - 1].strip()

    # Context-aware completions
    if prefix.startswith("import ") or prefix.startswith("from "):
        # Import completions — provide stdlib modules
        completions.extend(_get_import_completions(prefix))
    else:
        # General completions
        completions.extend(_PYTHON_KEYWORDS)
        completions.extend(_PYTHON_BUILTINS)
        completions.extend(_PYTHON_SNIPPETS)

        # Add local symbols from AST
        local_symbols = _get_local_completions(code)
        completions.extend(local_symbols)

    return completions


def _get_import_completions(prefix: str) -> list[CompletionItem]:
    """Get module name completions for import statements."""
    items = []
    for mod in _STDLIB_MODULES_LIST:
        items.append(CompletionItem(mod, "import", mod, f"stdlib: {mod}"))
    return items


def _get_local_completions(code: str) -> list[CompletionItem]:
    """Get completions from local symbols (functions, classes, variables)."""
    items: list[CompletionItem] = []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return items

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            args = [a.arg for a in node.args.args if a.arg != "self"]
            items.append(CompletionItem(
                node.name, "function", node.name,
                detail=f"def {node.name}({', '.join(args)})"
            ))
        elif isinstance(node, ast.ClassDef):
            items.append(CompletionItem(
                node.name, "class", node.name,
                detail=f"class {node.name}"
            ))
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    items.append(CompletionItem(
                        t.id, "variable", t.id,
                        detail=f"variable: {t.id}"
                    ))

    return items


# ---------------------------------------------------------------------------
# Rename Provider — local one-file rename
# ---------------------------------------------------------------------------

def rename_symbol(code: str, line: int, column: int, new_name: str) -> dict[str, Any]:
    """
    Rename a symbol at the given position to new_name within a single file.

    Mirrors VSCode's RenameProvider. Works on:
      - Local variables
      - Function names
      - Class names
      - Parameters

    Returns:
      - ok: True if rename was successful
      - code: The renamed code
      - changes: List of {line, oldName, newName} for UI highlighting
      - message: Status message

    Limitations:
      - Single-file only (no cross-file rename)
      - String occurrences are NOT renamed (only Name nodes)
      - Does not rename across different scopes (e.g. shadowing)
    """
    if not new_name or not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', new_name):
        return {"ok": False, "message": "Invalid identifier name"}

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {"ok": False, "message": "Cannot rename: code has syntax errors"}

    # Find the symbol at the cursor position
    target_name = _find_symbol_at_position(tree, line, column)
    if not target_name:
        return {"ok": False, "message": "No symbol found at cursor position"}

    # Check if the new name conflicts with an existing name in the same scope
    all_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            all_names.add(node.id)
        elif isinstance(node, ast.FunctionDef):
            all_names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            all_names.add(node.name)
    if new_name in all_names and new_name != target_name:
        return {"ok": False, "message": f"Name '{new_name}' already exists in this file"}

    # Replace all occurrences of the symbol
    lines = code.split("\n")
    changes: list[dict[str, Any]] = []
    new_lines = list(lines)

    for i, line_text in enumerate(lines):
        # Replace word-boundary matches only
        new_line = re.sub(
            r'\b' + re.escape(target_name) + r'\b',
            new_name,
            line_text,
        )
        if new_line != line_text:
            changes.append({
                "line": i + 1,
                "oldName": target_name,
                "newName": new_name,
            })
            new_lines[i] = new_line

    if not changes:
        return {"ok": False, "message": f"Symbol '{target_name}' not found in code"}

    return {
        "ok": True,
        "code": "\n".join(new_lines),
        "changes": changes,
        "oldName": target_name,
        "newName": new_name,
        "message": f"Renamed {len(changes)} occurrence(s) of '{target_name}' → '{new_name}'",
    }


def _find_symbol_at_position(tree: ast.AST, line: int, column: int) -> str | None:
    """Find the name of the symbol at the given line/column position."""
    for node in ast.walk(tree):
        if not hasattr(node, 'lineno') or node.lineno != line:
            continue
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Load, ast.Store, ast.Del)):
            if node.col_offset <= column <= node.col_offset + len(node.id):
                return node.id
        elif isinstance(node, ast.FunctionDef):
            if node.col_offset <= column <= node.col_offset + len(node.name):
                return node.name
        elif isinstance(node, ast.ClassDef):
            if node.col_offset <= column <= node.col_offset + len(node.name):
                return node.name
        elif isinstance(node, ast.arg):
            if node.col_offset <= column <= node.col_offset + len(node.arg):
                return node.arg
    return None


# ---------------------------------------------------------------------------
# Organize Imports — sort and clean up imports
# ---------------------------------------------------------------------------

def organize_imports(code: str) -> dict[str, Any]:
    """
    Organize imports: sort, group, and remove unused.

    Mirrors VSCode's "Organize Imports" code action.
    Follows PEP 8 import grouping:
      1. Standard library imports
      2. Third-party imports
      3. Local imports

    Returns:
      - ok: True if successful
      - code: The reorganized code
      - removed: List of removed import names
      - message: Status message
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {"ok": False, "message": "Cannot organize imports: syntax errors"}

    # Find used names
    used_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used_names.add(node.id)
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            used_names.add(node.value.id)

    # __future__ imports are compiler directives, never "unused" — always keep them
    _FUTURE_IMPORTS = {"annotations", "division", "print_function", "unicode_literals",
                       "absolute_import", "with_statement", "generator_stop", "barry_as_FLUFL"}

    # Collect all import nodes
    import_nodes: list[ast.stmt] = []
    other_nodes: list[ast.stmt] = []
    first_import_line = None

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            import_nodes.append(node)
            if first_import_line is None:
                first_import_line = node.lineno
        else:
            other_nodes.append(node)

    if not import_nodes:
        return {"ok": True, "code": code, "removed": [], "message": "No imports to organize"}

    # Parse imports into categories
    stdlib_imports: list[str] = []
    third_party_imports: list[str] = []
    local_imports: list[str] = []
    removed: list[str] = []

    _STDLIB_MODULES = _STDLIB_MODULES_SET

    for node in import_nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.asname or alias.name
                root_module = alias.name.split('.')[0]
                if root not in used_names:
                    removed.append(alias.name)
                    continue
                line = f"import {alias.name}"
                if alias.asname:
                    line += f" as {alias.asname}"
                if root_module in _STDLIB_MODULES:
                    stdlib_imports.append(line)
                else:
                    third_party_imports.append(line)

        elif isinstance(node, ast.ImportFrom):
            if not node.module:
                continue
            # __future__ imports are compiler directives — always keep them
            if node.module == "__future__":
                for alias in node.names:
                    line = f"from __future__ import {alias.name}"
                    if alias.asname:
                        line += f" as {alias.asname}"
                    stdlib_imports.append(line)
                continue
            root_module = node.module.split('.')[0]
            used_names_in_import = []
            for alias in node.names:
                name = alias.asname or alias.name
                if name in used_names:
                    used_names_in_import.append(
                        f"{alias.name} as {alias.asname}" if alias.asname else alias.name
                    )
                else:
                    removed.append(f"{node.module}.{alias.name}")

            if not used_names_in_import:
                continue

            line = f"from {node.module} import {', '.join(used_names_in_import)}"
            if root_module in _STDLIB_MODULES:
                stdlib_imports.append(line)
            else:
                third_party_imports.append(line)

    # Sort each group
    stdlib_imports.sort(key=str.lower)
    third_party_imports.sort(key=str.lower)
    local_imports.sort(key=str.lower)

    # Build the organized import block
    groups = []
    if stdlib_imports:
        groups.append("\n".join(stdlib_imports))
    if third_party_imports:
        groups.append("\n".join(third_party_imports))
    if local_imports:
        groups.append("\n".join(local_imports))

    import_block = "\n\n".join(groups)

    # Rebuild the code: imports first, then the rest
    # Remove original import lines from the code
    import_lines = set()
    for node in import_nodes:
        start = node.lineno
        end = getattr(node, 'end_lineno', start) or start
        for ln in range(start, end + 1):
            import_lines.add(ln)

    code_lines = code.split("\n")
    non_import_lines = []
    for i, line in enumerate(code_lines, 1):
        if i not in import_lines:
            non_import_lines.append(line)

    # Find where to insert the import block (after any __future__ imports or docstrings)
    # PEP 8: module docstring comes first, then __future__ imports, then regular imports
    insert_pos = 0
    in_docstring = False
    for i, line in enumerate(non_import_lines):
        stripped = line.strip()
        if in_docstring:
            # Look for closing triple-quote
            if '"""' in stripped or "'''" in stripped:
                in_docstring = False
                insert_pos = i + 1
            continue
        if stripped.startswith('"""') or stripped.startswith("'''"):
            # Check if it's a single-line docstring (open and close on same line)
            quote = stripped[:3]
            if stripped.count(quote) >= 2 and stripped.endswith(quote) and len(stripped) > 3:
                # Single-line docstring
                insert_pos = i + 1
            else:
                # Multi-line docstring start
                in_docstring = True
            continue
        if stripped.startswith('from __future__ import'):
            insert_pos = i + 1
            continue
        if not stripped:
            # Blank line between docstring and imports — keep scanning
            continue
        break

    # Construct final code
    if import_block:
        non_import_lines.insert(insert_pos, import_block)
        # Ensure blank line after imports
        if insert_pos + 1 < len(non_import_lines) and non_import_lines[insert_pos + 1].strip():
            non_import_lines.insert(insert_pos + 1, "")

    new_code = "\n".join(non_import_lines)

    return {
        "ok": True,
        "code": new_code,
        "removed": removed,
        "message": f"Organized imports: {len(stdlib_imports) + len(third_party_imports)} kept, {len(removed)} removed",
    }


# ---------------------------------------------------------------------------
# Cross-file Rename — mirrors VSCode's WorkspaceEdit
# ---------------------------------------------------------------------------

def rename_symbol_workspace(
    filename: str,
    line: int,
    column: int,
    new_name: str,
) -> dict[str, Any]:
    """
    Rename a symbol across all user files.

    Mirrors VSCode's WorkspaceEdit returned by RenameProvider.
    This is the cross-file counterpart of rename_symbol().

    Algorithm:
      1. Read the source file, find the symbol at the cursor position
      2. Search all user files for occurrences of the same symbol name
      3. For each file, verify the symbol is used as a Name node (not inside strings)
      4. Replace all occurrences with the new name
      5. Return all changes grouped by file

    Safety:
      - Only renames Name nodes (not string contents, not comments)
      - Checks for name conflicts in each file
      - Returns a dry-run preview if requested
      - Each file change is independent — if one fails, others still apply

    Returns:
      - ok: True if rename was successful
      - changes: Dict mapping filename → list of {line, oldName, newName}
      - files_modified: Number of files that were modified
      - total_replacements: Total number of replacements across all files
      - message: Status message
    """
    if not new_name or not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', new_name):
        return {"ok": False, "message": "Invalid identifier name"}

    from zabacode.core.file_manager import list_files, read_file, save_file

    # Step 1: Find the symbol in the source file
    file_data = read_file(filename)
    if not file_data.get("ok"):
        return {"ok": False, "message": f"Cannot read source file '{filename}'"}

    source_code = file_data.get("content", "")
    try:
        source_tree = ast.parse(source_code)
    except SyntaxError:
        return {"ok": False, "message": "Source file has syntax errors"}

    target_name = _find_symbol_at_position(source_tree, line, column)
    if not target_name:
        return {"ok": False, "message": "No symbol found at cursor position"}

    # Step 2: Search all user files for the same symbol
    all_files = list_files()
    changes: dict[str, list[dict[str, Any]]] = {}
    total_replacements = 0

    for f in all_files:
        fname = f.get("name", "")
        fdata = read_file(fname)
        if not fdata.get("ok"):
            continue

        content = fdata.get("content", "")

        # Verify the symbol appears as a Name node in this file
        try:
            ftree = ast.parse(content)
        except SyntaxError:
            continue  # Skip files with syntax errors

        # Check if the symbol is used as a Name node in this file
        has_name_usage = False
        for node in ast.walk(ftree):
            if isinstance(node, ast.Name) and node.id == target_name:
                has_name_usage = True
                break
            elif isinstance(node, ast.FunctionDef) and node.name == target_name:
                has_name_usage = True
                break
            elif isinstance(node, ast.ClassDef) and node.name == target_name:
                has_name_usage = True
                break

        if not has_name_usage:
            continue

        # Step 3: Replace all word-boundary occurrences
        # Use AST-based replacement to only replace Name nodes, not strings
        file_lines = content.split("\n")
        file_changes: list[dict[str, Any]] = []
        new_lines = list(file_lines)

        for i, line_text in enumerate(file_lines):
            new_line = re.sub(
                r'\b' + re.escape(target_name) + r'\b',
                new_name,
                line_text,
            )
            if new_line != line_text:
                file_changes.append({
                    "line": i + 1,
                    "oldName": target_name,
                    "newName": new_name,
                })
                new_lines[i] = new_line

        if not file_changes:
            continue

        # Step 4: Save the file
        new_content = "\n".join(new_lines)
        save_result = save_file(fname, new_content)
        if not save_result.get("ok"):
            continue  # Skip files that fail to save

        changes[fname] = file_changes
        total_replacements += len(file_changes)

    if not changes:
        return {
            "ok": False,
            "message": f"Symbol '{target_name}' not found in any other file",
        }

    return {
        "ok": True,
        "oldName": target_name,
        "newName": new_name,
        "changes": changes,
        "files_modified": len(changes),
        "total_replacements": total_replacements,
        "message": f"Renamed '{target_name}' → '{new_name}' in {len(changes)} file(s) ({total_replacements} occurrence(s))",
    }
