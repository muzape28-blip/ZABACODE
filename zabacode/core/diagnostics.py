"""
ZABACODE Core — Diagnostics Engine (Inspired by VSCode's Diagnostic Collection)

VSCode's diagnostic system (src/vs/editor/common/services/diagnostics.ts) provides:
  - DiagnosticCollection: a named collection of diagnostics per URI
  - Diagnostics are typed (Error, Warning, Info, Hint) with severity levels
  - Multiple providers can contribute diagnostics to the same collection
  - The Problems panel aggregates all diagnostics across all collections

We port this to Python:
  - Diagnostic: a single diagnostic item (severity, message, range, source)
  - DiagnosticCollection: a named collection of diagnostics
  - DiagnosticEngine: aggregates diagnostics from all sources
  - QuickFix: a code action that can resolve a diagnostic

References:
  - https://github.com/microsoft/vscode/blob/main/src/vs/editor/common/services/diagnostics.ts
  - https://code.visualstudio.com/api/references/vscode-api#Diagnostic
"""

from __future__ import annotations

import ast
import enum
import threading
from dataclasses import dataclass, field
from typing import Any, Callable

from zabacode.core.events import Emitter, IDisposable


# ---------------------------------------------------------------------------
# Diagnostic Severity — mirrors VSCode's DiagnosticSeverity
# ---------------------------------------------------------------------------

class DiagnosticSeverity(enum.IntEnum):
    """Severity levels for diagnostics — mirrors VSCode's DiagnosticSeverity."""
    HINT = 0
    INFORMATION = 1
    WARNING = 2
    ERROR = 3


class DiagnosticTag(enum.IntEnum):
    """Tags for diagnostics — mirrors VSCode's DiagnosticTag."""
    UNNECESSARY = 1  # Unused code (e.g. unused imports)
    DEPRECATED = 2   # Deprecated code


# ---------------------------------------------------------------------------
# Diagnostic — mirrors VSCode's Diagnostic class
# ---------------------------------------------------------------------------

@dataclass
class Diagnostic:
    """
    A single diagnostic item — mirrors VSCode's Diagnostic.

    Attributes:
        line: 1-based line number
        column: 1-based column number (character offset)
        end_line: 1-based end line (inclusive)
        end_column: 1-based end column (inclusive)
        severity: Error, Warning, Info, or Hint
        message: Human-readable description
        source: Who produced this (e.g. "checker", "oracle", "linter")
        code: Machine-readable identifier (e.g. "E0602", "unused-import")
        tags: Optional tags (unnecessary, deprecated)
        quick_fixes: Available quick fixes for this diagnostic
    """
    line: int
    column: int
    message: str
    severity: DiagnosticSeverity = DiagnosticSeverity.ERROR
    end_line: int | None = None
    end_column: int | None = None
    source: str = "zabacode"
    code: str | None = None
    tags: list[DiagnosticTag] = field(default_factory=list)
    quick_fixes: list[QuickFix] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        d: dict[str, Any] = {
            "line": self.line,
            "column": self.column,
            "endLine": self.end_line or self.line,
            "endColumn": self.end_column or self.column,
            "severity": int(self.severity),
            "severityLabel": _SEVERITY_LABELS.get(self.severity, "???"),
            "message": self.message,
            "source": self.source,
        }
        if self.code is not None:
            d["code"] = self.code
        if self.tags:
            d["tags"] = [int(t) for t in self.tags]
        if self.quick_fixes:
            d["quickFixes"] = [qf.to_dict() for qf in self.quick_fixes]
        return d


_SEVERITY_LABELS = {
    DiagnosticSeverity.HINT: "HINT",
    DiagnosticSeverity.INFORMATION: "INFO",
    DiagnosticSeverity.WARNING: "WARN",
    DiagnosticSeverity.ERROR: "ERROR",
}


# ---------------------------------------------------------------------------
# QuickFix — mirrors VSCode's CodeAction
# ---------------------------------------------------------------------------

@dataclass
class QuickFix:
    """
    A quick fix for a diagnostic — mirrors VSCode's CodeAction.

    Attributes:
        title: Human-readable title (e.g. "Add missing colon")
        action: The command ID to execute (registered in CommandRegistry)
        args: Arguments for the command
        is_preferred: Whether this is the preferred fix
    """
    title: str
    action: str
    args: list[Any] = field(default_factory=list)
    is_preferred: bool = False

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "title": self.title,
            "action": self.action,
            "args": self.args,
            "isPreferred": self.is_preferred,
        }
        return d


# ---------------------------------------------------------------------------
# DiagnosticCollection — mirrors VSCode's DiagnosticCollection
# ---------------------------------------------------------------------------

class DiagnosticCollection:
    """
    A named collection of diagnostics — mirrors VSCode's DiagnosticCollection.

    Multiple providers can own their own collection (e.g. "oracle", "checker",
    "linter"). The DiagnosticEngine aggregates all collections.

    Usage:
        engine = get_diagnostic_engine()
        collection = engine.create_collection("my-linter")
        collection.set([
            Diagnostic(line=5, column=1, message="Unused import 'os'",
                       severity=DiagnosticSeverity.WARNING, code="unused-import",
                       tags=[DiagnosticTag.UNNECESSARY])
        ])
        # Later:
        collection.clear()
    """

    def __init__(self, name: str, engine: DiagnosticEngine) -> None:
        self._name = name
        self._engine = engine
        self._diagnostics: list[Diagnostic] = []
        self._lock = threading.Lock()

    @property
    def name(self) -> str:
        return self._name

    def set(self, diagnostics: list[Diagnostic]) -> None:
        """Replace all diagnostics in this collection."""
        with self._lock:
            self._diagnostics = list(diagnostics)
        self._engine._on_collection_changed(self)

    def get(self) -> list[Diagnostic]:
        """Get all diagnostics in this collection."""
        with self._lock:
            return list(self._diagnostics)

    def clear(self) -> None:
        """Remove all diagnostics from this collection."""
        self.set([])

    def dispose(self) -> None:
        """Remove this collection from the engine."""
        self._engine._remove_collection(self)


# ---------------------------------------------------------------------------
# DiagnosticEngine — aggregates all diagnostic collections
# ---------------------------------------------------------------------------

class DiagnosticEngine:
    """
    Central diagnostic aggregator — mirrors VSCode's diagnostic service.

    Collects diagnostics from all registered collections and provides:
      - Aggregated diagnostics across all sources
      - Event emission when diagnostics change
      - Quick-fix resolution via the command registry
      - Backend diagnostics from AST analysis (checker + oracle integration)

    Usage:
        engine = get_diagnostic_engine()
        collection = engine.create_collection("oracle")
        collection.set([Diagnostic(...)])
        all_diags = engine.get_all_diagnostics()
    """

    def __init__(self) -> None:
        self._collections: dict[str, DiagnosticCollection] = {}
        self._lock = threading.Lock()
        self._onDidChangeDiagnostics = Emitter[list[Diagnostic]]()
        self.onDidChangeDiagnostics = self._onDidChangeDiagnostics.event

    def create_collection(self, name: str) -> DiagnosticCollection:
        """Create a new named diagnostic collection."""
        with self._lock:
            if name in self._collections:
                return self._collections[name]
            collection = DiagnosticCollection(name, self)
            self._collections[name] = collection
            return collection

    def _remove_collection(self, collection: DiagnosticCollection) -> None:
        """Remove a collection (called on dispose)."""
        with self._lock:
            self._collections.pop(collection.name, None)
        self._fire_changed()

    def _on_collection_changed(self, collection: DiagnosticCollection) -> None:
        """Called when a collection's diagnostics change."""
        self._fire_changed()

    def _fire_changed(self) -> None:
        """Fire the change event with the current aggregated diagnostics."""
        all_diags = self.get_all_diagnostics()
        self._onDidChangeDiagnostics.fire(all_diags)

    def get_all_diagnostics(self) -> list[Diagnostic]:
        """Get all diagnostics from all collections, sorted by line then severity."""
        diags: list[Diagnostic] = []
        with self._lock:
            for collection in self._collections.values():
                diags.extend(collection.get())
        # Sort: errors first, then by line number
        diags.sort(key=lambda d: (d.line, -d.severity))
        return diags

    def get_diagnostics_by_source(self, source: str) -> list[Diagnostic]:
        """Get diagnostics from a specific source/collection."""
        with self._lock:
            collection = self._collections.get(source)
            if collection:
                return collection.get()
        return []

    def get_diagnostics_severity_counts(self) -> dict[str, int]:
        """Get counts by severity level."""
        diags = self.get_all_diagnostics()
        counts = {"error": 0, "warning": 0, "info": 0, "hint": 0}
        for d in diags:
            if d.severity == DiagnosticSeverity.ERROR:
                counts["error"] += 1
            elif d.severity == DiagnosticSeverity.WARNING:
                counts["warning"] += 1
            elif d.severity == DiagnosticSeverity.INFORMATION:
                counts["info"] += 1
            elif d.severity == DiagnosticSeverity.HINT:
                counts["hint"] += 1
        return counts

    def dispose(self) -> None:
        """Dispose all collections and the engine."""
        with self._lock:
            self._collections.clear()
        self._onDidChangeDiagnostics.dispose()


# ---------------------------------------------------------------------------
# AST-based Diagnostic Providers — produce diagnostics from code analysis
# ---------------------------------------------------------------------------

def analyze_code_diagnostics(code: str) -> list[Diagnostic]:
    """
    Produce diagnostics from Python code using AST analysis.

    Combines:
      1. Syntax errors (from compile)
      2. Checker findings (from checker module)
      3. Oracle-style pattern analysis (unused imports, etc.)

    Returns a list of Diagnostic objects with quick-fixes where applicable.
    """
    diagnostics: list[Diagnostic] = []

    # 1. Syntax check via compile()
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        diag = Diagnostic(
            line=e.lineno or 1,
            column=e.offset or 1,
            end_line=e.end_lineno or e.lineno or 1,
            end_column=e.end_offset or e.offset or 1,
            message=e.msg or "Syntax error",
            severity=DiagnosticSeverity.ERROR,
            source="syntax",
            code="syntax-error",
        )
        # Add Auto-Fix quick fix
        diag.quick_fixes.append(QuickFix(
            title="🔧 Auto-Fix with Oracle",
            action="zabacode.oracle.fix",
            is_preferred=True,
        ))
        diagnostics.append(diag)
        return diagnostics  # Can't analyze further with syntax errors

    # 2. Checker findings (bracket imbalance, etc.)
    from zabacode.core.checker import check_code
    check_result = check_code(code)
    if not check_result.get("valid", True):
        for i, issue in enumerate(check_result.get("issues", [])):
            # Try to extract line number from the issue string
            line_num = _extract_line_number(issue)
            diag = Diagnostic(
                line=line_num,
                column=1,
                message=issue,
                severity=DiagnosticSeverity.WARNING,
                source="checker",
                code=f"checker-{i}",
            )
            diag.quick_fixes.append(QuickFix(
                title="🔧 Auto-Fix with Oracle",
                action="zabacode.oracle.fix",
            ))
            diagnostics.append(diag)

    # 3. AST-based analysis (unused imports, unreachable code, etc.)
    diagnostics.extend(_analyze_ast(tree, code))

    return diagnostics


def _extract_line_number(issue_text: str) -> int:
    """Try to extract a line number from a checker issue string."""
    import re
    match = re.search(r"Line (\d+)", issue_text)
    if match:
        return int(match.group(1))
    return 1


def _analyze_ast(tree: ast.AST, code: str) -> list[Diagnostic]:
    """Produce diagnostics from AST analysis."""
    diagnostics: list[Diagnostic] = []

    # 3a. Unused imports
    imported_names: dict[str, tuple[int, int, str]] = {}
    used_names: set[str] = set()

    class ImportVisitor(ast.NodeVisitor):
        def visit_Import(self, node):
            for alias in node.names:
                name = alias.asname or alias.name
                root_name = name.split('.')[0]
                imported_names[root_name] = (node.lineno, node.col_offset + 1, name)
            self.generic_visit(node)

        def visit_ImportFrom(self, node):
            for alias in node.names:
                name = alias.asname or alias.name
                imported_names[name] = (node.lineno, node.col_offset + 1, f"from {node.module} import {name}")
            self.generic_visit(node)

        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Load):
                used_names.add(node.id)
            self.generic_visit(node)

    visitor = ImportVisitor()
    visitor.visit(tree)

    for name, (line, col, full_name) in imported_names.items():
        if name not in used_names:
            diag = Diagnostic(
                line=line,
                column=col,
                message=f"Unused import '{full_name}'",
                severity=DiagnosticSeverity.WARNING,
                source="linter",
                code="unused-import",
                tags=[DiagnosticTag.UNNECESSARY],
            )
            diag.quick_fixes.append(QuickFix(
                title=f"Remove unused import '{full_name}'",
                action="zabacode.plugin.auto_import_optimizer",
                is_preferred=True,
            ))
            diagnostics.append(diag)

    # 3b. Function/method without docstring
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if ast.get_docstring(node) is None and not node.name.startswith("_"):
                diag = Diagnostic(
                    line=node.lineno,
                    column=node.col_offset + 1,
                    message=f"Function '{node.name}' has no docstring",
                    severity=DiagnosticSeverity.HINT,
                    source="linter",
                    code="missing-docstring",
                )
                diag.quick_fixes.append(QuickFix(
                    title=f"Generate docstring for '{node.name}'",
                    action="zabacode.plugin.smart_comment_generator",
                ))
                diagnostics.append(diag)

    # 3c. bare 'except:' clauses
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            diag = Diagnostic(
                line=node.lineno,
                column=node.col_offset + 1,
                message="Bare 'except:' catches all exceptions including KeyboardInterrupt",
                severity=DiagnosticSeverity.WARNING,
                source="linter",
                code="bare-except",
            )
            diagnostics.append(diag)

    return diagnostics


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_engine: DiagnosticEngine | None = None
_engine_lock = threading.Lock()


def get_diagnostic_engine() -> DiagnosticEngine:
    """Get or create the global DiagnosticEngine singleton."""
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = DiagnosticEngine()
    return _engine
