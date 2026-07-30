"""Shared Diagnostic schema for ZABACODE (inspired by VS Code Diagnostic model).

This module defines a canonical, language-agnostic diagnostic format used by:
- Oracle (analyze_buffer, humanize_traceback)
- Checker
- Future language servers / plugins

Reference: https://github.com/microsoft/vscode/blob/main/src/vs/workbench/contrib/markers/common/markers.ts
and https://github.com/microsoft/vscode-languageserver-node types.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Any, Dict, List, Literal, Optional, TypedDict


class DiagnosticSeverity(IntEnum):
    """Matches VS Code DiagnosticSeverity."""
    Error = 0
    Warning = 1
    Information = 2
    Hint = 3


class DiagnosticTag(IntEnum):
    """Matches VS Code DiagnosticTag."""
    Unnecessary = 1
    Deprecated = 2


class Range(TypedDict):
    """Zero-based, inclusive start / exclusive end (VS Code convention)."""
    startLine: int
    startColumn: int
    endLine: int
    endColumn: int


class DiagnosticRelatedInformation(TypedDict, total=False):
    location: Dict[str, Any]  # { uri: str, range: Range }
    message: str


class Diagnostic(TypedDict, total=False):
    """
    Canonical diagnostic object used across ZABACODE.

    Fields are kept close to the VS Code Diagnostic shape for easy future
    integration with Monaco / Ace / Language Server Protocol.
    """
    # Required core fields
    range: Range
    message: str
    severity: int  # DiagnosticSeverity

    # Optional rich metadata
    source: Optional[str]          # e.g. "oracle", "checker", "pyright"
    code: Optional[str | int]      # error code, e.g. "E1120" or "syntax-error"
    tags: Optional[List[int]]      # list of DiagnosticTag
    relatedInformation: Optional[List[DiagnosticRelatedInformation]]

    # ZABACODE-specific extensions (non-breaking)
    fixable: Optional[bool]        # whether Oracle can produce a quick-fix
    quickFixId: Optional[str]      # id for CodeActionRule registry
    explanation: Optional[str]     # human-friendly explanation (from Oracle)


# Convenience factory
def make_diagnostic(
    start_line: int,
    start_col: int,
    end_line: int,
    end_col: int,
    message: str,
    severity: DiagnosticSeverity = DiagnosticSeverity.Error,
    source: str = "oracle",
    code: Optional[str | int] = None,
    fixable: bool = False,
    quick_fix_id: Optional[str] = None,
    explanation: Optional[str] = None,
) -> Diagnostic:
    """Helper to create a well-formed Diagnostic."""
    return {
        "range": {
            "startLine": start_line,
            "startColumn": start_col,
            "endLine": end_line,
            "endColumn": end_col,
        },
        "message": message,
        "severity": int(severity),
        "source": source,
        "code": code,
        "fixable": fixable,
        "quickFixId": quick_fix_id,
        "explanation": explanation,
    }


def diagnostics_to_ace_annotations(diagnostics: List[Diagnostic]) -> List[Dict[str, Any]]:
    """
    Convert our Diagnostic list into Ace Editor annotation format.
    Ace uses: { row, column, text, type }
    type can be 'error', 'warning', 'info'
    """
    annotations = []
    for d in diagnostics:
        r = d.get("range", {})
        sev = d.get("severity", 0)
        ann_type = "error" if sev == 0 else ("warning" if sev == 1 else "info")

        annotations.append({
            "row": r.get("startLine", 0),
            "column": r.get("startColumn", 0),
            "text": d.get("message", ""),
            "type": ann_type,
        })
    return annotations


def get_severity_name(severity: int) -> str:
    names = {0: "Error", 1: "Warning", 2: "Information", 3: "Hint"}
    return names.get(severity, "Unknown")
