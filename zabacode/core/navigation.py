"""
ZABACODE Core — Navigation & Workspace (Inspired by VSCode's Quick Open & Workspace)

VSCode's navigation features:
  - Command Palette: Ctrl+Shift+P → search and execute any command
  - Quick Open: Ctrl+P → search and open files by name
  - Searchable Settings: Ctrl+, → search settings by keyword
  - Workspace: folder model, project search, cross-file symbols

We port these to Python for a mobile IDE context.

References:
  - https://github.com/microsoft/vscode/blob/main/src/vs/workbench/contrib/quickopen/
  - https://code.visualstudio.com/docs/getstarted/keybindings#_command-palette
"""

from __future__ import annotations

import re
import json
from dataclasses import dataclass, field
from typing import Any

from zabacode.core.commands import get_command_registry
from zabacode.core.file_manager import list_files, read_file
from zabacode.core.editor_intelligence import find_symbol, get_symbol_outline, _SYMBOL_KIND_LABELS


# ---------------------------------------------------------------------------
# Command Palette — mirrors VSCode's Command Palette
# ---------------------------------------------------------------------------

@dataclass
class PaletteItem:
    """An item in the command palette."""
    label: str
    category: str
    detail: str
    action: str  # command ID or special action
    args: list[Any] = field(default_factory=list)
    score: float = 0.0  # fuzzy match score

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "category": self.category,
            "detail": self.detail,
            "action": self.action,
            "args": self.args,
        }


def get_command_palette_items(query: str = "") -> list[PaletteItem]:
    """
    Get all command palette items, filtered by query.

    Mirrors VSCode's Command Palette (Ctrl+Shift+P).
    Returns:
      - All registered commands
      - File operations (new, open, save)
      - Editor actions (format, lint, run)
      - Navigation actions (outline, symbols, settings)
    """
    items: list[PaletteItem] = []

    # 1. All registered commands
    registry = get_command_registry()
    for cmd_id in registry.get_command_ids():
        meta = registry.get_command_metadata(cmd_id) or {}
        name = meta.get("name", cmd_id.split(".")[-1].replace("_", " ").title())
        category = meta.get("category", cmd_id.split(".")[-2].title() if "." in cmd_id else "General")
        items.append(PaletteItem(
            label=name,
            category=category,
            detail=cmd_id,
            action="command",
            args=[cmd_id],
        ))

    # 2. File operations
    items.extend([
        PaletteItem("New File", "File", "Create a new Python file", "file.new"),
        PaletteItem("Open File", "File", "Open an existing file", "file.open"),
        PaletteItem("Save File", "File", "Save the current file", "file.save"),
        PaletteItem("Delete File", "File", "Delete the current file", "file.delete"),
    ])

    # 3. Editor actions
    items.extend([
        PaletteItem("Run Code", "Run", "Execute the current code", "run.code"),
        PaletteItem("Run Interactive", "Run", "Start interactive session", "run.interactive"),
        PaletteItem("Stop Execution", "Run", "Stop the running process", "run.stop"),
        PaletteItem("Check Syntax", "Edit", "Check code for syntax errors", "edit.check"),
        PaletteItem("Auto-Fix with Oracle", "Edit", "Automatically fix code issues", "edit.autofix"),
        PaletteItem("Format Code (PEP-8)", "Edit", "Format code to PEP-8 standards", "edit.format"),
        PaletteItem("Organize Imports", "Edit", "Sort and remove unused imports", "edit.organize_imports"),
    ])

    # 4. Navigation
    items.extend([
        PaletteItem("Go to Symbol", "Navigate", "Jump to a symbol in the current file", "navigate.symbol"),
        PaletteItem("Go to Line", "Navigate", "Jump to a specific line number", "navigate.line"),
        PaletteItem("Quick Open File", "Navigate", "Quickly open a file by name", "navigate.quickopen"),
        PaletteItem("Show Outline", "Navigate", "Show the document symbol outline", "navigate.outline"),
        PaletteItem("Show Problems", "View", "Show the diagnostics panel", "view.problems"),
        PaletteItem("Toggle Terminal", "View", "Toggle the output terminal", "view.terminal"),
    ])

    # 5. AI
    items.extend([
        PaletteItem("AI Chat", "AI", "Open AI chat assistant", "ai.chat"),
        PaletteItem("Explain Error", "AI", "Explain the last error in plain language", "ai.explain"),
        PaletteItem("Analyze Code", "AI", "Analyze the current code buffer", "ai.analyze"),
    ])

    # 6. Settings
    items.extend([
        PaletteItem("Change Theme", "Settings", "Change the editor color theme", "settings.theme"),
        PaletteItem("Change AI Provider", "Settings", "Change the AI provider", "settings.ai_provider"),
        PaletteItem("Manage Libraries", "Settings", "Install and manage Python libraries", "settings.libraries"),
        PaletteItem("Manage Plugins", "Settings", "Toggle and configure plugins", "settings.plugins"),
        PaletteItem("Search Settings", "Settings", "Search all settings", "settings.search"),
    ])

    # Filter by query
    if query:
        items = _fuzzy_filter(items, query)

    return items


# ---------------------------------------------------------------------------
# Quick Open — mirrors VSCode's Quick Open (Ctrl+P)
# ---------------------------------------------------------------------------

@dataclass
class QuickOpenItem:
    """An item in Quick Open."""
    label: str
    detail: str
    action: str
    args: list[Any] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "detail": self.detail,
            "action": self.action,
            "args": self.args,
        }


def get_quick_open_items(query: str = "") -> list[QuickOpenItem]:
    """
    Get Quick Open items — files and symbols matching the query.

    Mirrors VSCode's Quick Open (Ctrl+P):
      - Type a filename to open it
      - Type @ to search symbols in the current file
      - Type : to go to a line number
    """
    items: list[QuickOpenItem] = []

    if query.startswith("@"):
        # Symbol search mode
        symbol_query = query[1:]
        # We need the current code to search symbols
        # The frontend will provide it; for now return empty
        # and the frontend will call /api/editor/symbols with the query
        items.append(QuickOpenItem(
            label=f"Search symbols: '{symbol_query}'",
            detail="Search for symbols in the current file",
            action="navigate.symbol",
            args=[symbol_query],
        ))
    elif query.startswith(":"):
        # Go to line mode
        line_str = query[1:].strip()
        if line_str.isdigit():
            items.append(QuickOpenItem(
                label=f"Go to line {line_str}",
                detail=f"Jump to line {line_str}",
                action="navigate.line",
                args=[int(line_str)],
            ))
    else:
        # File search mode
        files = list_files()
        for f in files:
            name = f.get("name", "")
            if not query or query.lower() in name.lower():
                size = f.get("size", 0)
                items.append(QuickOpenItem(
                    label=name,
                    detail=f"{size} bytes",
                    action="file.open",
                    args=[name],
                ))

    return items


# ---------------------------------------------------------------------------
# Searchable Settings — mirrors VSCode's Settings Editor
# ---------------------------------------------------------------------------

from zabacode.core.paths import APP_DIR

SETTINGS_FILE = APP_DIR / ".zabacode_settings.json"


def load_settings() -> dict[str, Any]:
    """Load settings from local JSON file."""
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_setting(key: str, value: Any) -> None:
    """Save a setting value to local JSON file."""
    settings = load_settings()
    settings[key] = value
    try:
        SETTINGS_FILE.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    except Exception:
        pass


@dataclass
class SettingItem:
    """A single setting."""
    key: str
    label: str
    category: str
    type: str  # "string", "number", "boolean", "select"
    default: Any
    current: Any
    options: list[str] = field(default_factory=list)  # for "select" type
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "category": self.category,
            "type": self.type,
            "default": self.default,
            "current": self.current,
            "options": self.options,
            "description": self.description,
        }


def get_all_settings(query: str = "") -> list[SettingItem]:
    """
    Get all settings, optionally filtered by query.

    Mirrors VSCode's searchable settings editor (Ctrl+,).
    """
    stored = load_settings()
    settings: list[SettingItem] = [
        # Editor
        SettingItem("editor.fontSize", "Font Size", "Editor", "number", 14, stored.get("editor.fontSize", 14),
                    description="Editor font size in pixels"),
        SettingItem("editor.tabSize", "Tab Size", "Editor", "number", 4, stored.get("editor.tabSize", 4),
                    description="Number of spaces per tab"),
        SettingItem("editor.wordWrap", "Word Wrap", "Editor", "boolean", True, stored.get("editor.wordWrap", True),
                    description="Wrap long lines"),
        SettingItem("editor.showLineNumbers", "Line Numbers", "Editor", "boolean", True, stored.get("editor.showLineNumbers", True),
                    description="Show line numbers in the gutter"),
        SettingItem("editor.minimap", "Minimap", "Editor", "boolean", False, stored.get("editor.minimap", False),
                    description="Show minimap on the right side"),
        SettingItem("editor.autoComplete", "Auto Complete", "Editor", "boolean", True, stored.get("editor.autoComplete", True),
                    description="Enable autocomplete suggestions"),

        # Appearance
        SettingItem("editor.theme", "Color Theme", "Appearance", "select", "retro", stored.get("editor.theme", "retro"),
                    options=["retro", "solarized", "dracula", "cyberpunk", "nord", "monokai",
                             "tokyo_night", "one_dark", "gruvbox", "catppuccin", "forest", "synthwave84"],
                    description="Editor color theme"),
        SettingItem("editor.engine", "Editor Engine", "Appearance", "select", "ace", stored.get("editor.engine", "ace"),
                    options=["ace", "native"],
                    description="Code editor engine (Ace or native textarea)"),
        SettingItem("editor.crtEffect", "CRT Effect", "Appearance", "boolean", False, stored.get("editor.crtEffect", False),
                    description="Enable CRT scanline effect"),

        # AI
        SettingItem("ai.provider", "AI Provider", "AI", "select", "openrouter", stored.get("ai.provider", "openrouter"),
                    options=["openrouter", "gemini", "groq", "mistral", "deepseek", "ollama", "custom"],
                    description="AI chat provider"),
        SettingItem("ai.model", "AI Model", "AI", "string", "", stored.get("ai.model", ""),
                    description="AI model name (leave empty for default)"),
        SettingItem("ai.allowOffline", "Allow Offline Fallback", "AI", "boolean", True, stored.get("ai.allowOffline", True),
                    description="Fall back to Oracle when cloud AI is unavailable"),

        # Execution
        SettingItem("run.timeout", "Execution Timeout", "Execution", "number", 30, stored.get("run.timeout", 30),
                    description="Maximum code execution time in seconds"),
        SettingItem("run.interactiveTimeout", "Interactive Timeout", "Execution", "number", 120, stored.get("run.interactiveTimeout", 120),
                    description="Maximum interactive session duration in seconds"),

        # Plugins
        SettingItem("plugins.autoFormatter", "Auto Formatter", "Plugins", "boolean", True, stored.get("plugins.autoFormatter", True),
                    description="Enable the PEP-8 auto-code formatter"),
        SettingItem("plugins.snippetPack", "Snippet Pack", "Plugins", "boolean", True, stored.get("plugins.snippetPack", True),
                    description="Enable the Pro Python Snippets Pack"),
        SettingItem("plugins.syntaxLinter", "Syntax Linter", "Plugins", "boolean", True, stored.get("plugins.syntaxLinter", True),
                    description="Enable the static syntax linter guard"),
        SettingItem("plugins.symbolBar", "Symbol Bar", "Plugins", "boolean", True, stored.get("plugins.symbolBar", True),
                    description="Enable the extended mobile symbol bar"),
    ]

    if query:
        query_lower = query.lower()
        settings = [s for s in settings
                    if query_lower in s.label.lower()
                    or query_lower in s.key.lower()
                    or query_lower in s.category.lower()
                    or query_lower in s.description.lower()]

    return settings


# ---------------------------------------------------------------------------
# Project Search — mirrors VSCode's Search in Files
# ---------------------------------------------------------------------------

@dataclass
class SearchResult:
    """A search result from project search."""
    filename: str
    line: int
    column: int
    line_text: str
    match_start: int
    match_end: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "line": self.line,
            "column": self.column,
            "lineText": self.line_text,
            "matchStart": self.match_start,
            "matchEnd": self.match_end,
        }


def search_in_files(query: str, case_sensitive: bool = False, regex: bool = False) -> list[SearchResult]:
    """
    Search for a string across all user files.

    Mirrors VSCode's Search in Files (Ctrl+Shift+F).
    """
    if not query:
        return []

    results: list[SearchResult] = []

    files = list_files()
    for f in files:
        name = f.get("name", "")
        file_data = read_file(name)
        if not file_data.get("ok"):
            continue

        content = file_data.get("content", "")
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            if regex:
                try:
                    matches = list(re.finditer(query, line, 0 if case_sensitive else re.IGNORECASE))
                except re.error:
                    continue
            else:
                flags = 0 if case_sensitive else re.IGNORECASE
                matches = list(re.finditer(re.escape(query), line, flags))

            for match in matches:
                results.append(SearchResult(
                    filename=name,
                    line=i,
                    column=match.start() + 1,
                    line_text=line.rstrip(),
                    match_start=match.start(),
                    match_end=match.end(),
                ))

    return results


# ---------------------------------------------------------------------------
# Cross-file Symbol Index — mirrors VSCode's workspace/symbol
# ---------------------------------------------------------------------------

@dataclass
class WorkspaceSymbol:
    """A symbol from across the workspace."""
    name: str
    kind: str
    filename: str
    line: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "filename": self.filename,
            "line": self.line,
        }


def get_workspace_symbols(query: str = "") -> list[WorkspaceSymbol]:
    """
    Get all symbols across all user files.

    Mirrors VSCode's workspace/symbol endpoint (Ctrl+T).
    """
    symbols: list[WorkspaceSymbol] = []

    files = list_files()
    for f in files:
        name = f.get("name", "")
        file_data = read_file(name)
        if not file_data.get("ok"):
            continue

        content = file_data.get("content", "")
        file_symbols = find_symbol(content, query)

        for sym in file_symbols:
            symbols.append(WorkspaceSymbol(
                name=sym.name,
                kind=_SYMBOL_KIND_LABELS.get(sym.kind, "symbol"),
                filename=name,
                line=sym.line,
            ))

    return symbols


# ---------------------------------------------------------------------------
# Import Graph — analyze imports across files
# ---------------------------------------------------------------------------

def get_import_graph() -> dict[str, list[str]]:
    """
    Build an import graph from all user files.

    Returns a dict mapping filename → list of imported modules.
    """
    graph: dict[str, list[str]] = {}

    files = list_files()
    for f in files:
        name = f.get("name", "")
        file_data = read_file(name)
        if not file_data.get("ok"):
            continue

        content = file_data.get("content", "")
        try:
            import ast as _ast
            tree = _ast.parse(content)
            imports = []
            for node in _ast.walk(tree):
                if isinstance(node, _ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, _ast.ImportFrom) and node.module:
                    imports.append(node.module)
            graph[name] = sorted(set(imports))
        except SyntaxError:
            graph[name] = []

    return graph


# ---------------------------------------------------------------------------
# Fuzzy matching helper
# ---------------------------------------------------------------------------

def _fuzzy_filter(items: list[PaletteItem], query: str) -> list[PaletteItem]:
    """Simple fuzzy filter for palette items."""
    query_lower = query.lower()
    scored = []
    for item in items:
        text = f"{item.label} {item.category} {item.detail}".lower()
        if query_lower in text:
            # Exact substring match = highest score
            item.score = 10.0
            scored.append(item)
        elif _fuzzy_match(query_lower, text):
            item.score = 5.0
            scored.append(item)

    scored.sort(key=lambda x: x.score, reverse=True)
    return scored


def _fuzzy_match(query: str, text: str) -> bool:
    """Check if query characters appear in order in text."""
    qi = 0
    for ch in text:
        if qi < len(query) and ch == query[qi]:
            qi += 1
    return qi == len(query)
