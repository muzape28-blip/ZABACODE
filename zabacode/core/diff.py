"""Small, bounded line-diff helper for safe editor patch previews."""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import TypedDict

# A complete dynamic diff for a very large accidental paste can cost too much
# memory/CPU on a phone. Auto-Fix still works; the UI receives an honest,
# simplified preview instead of a misleading positional line comparison.
MAX_DIFF_LINES = 5_000


class LineChange(TypedDict):
    type: str
    old_start: int
    old_end: int
    new_start: int
    new_end: int


class LineDiff(TypedDict):
    truncated: bool
    changes: list[LineChange]


def compute_line_diff(before: str, after: str) -> LineDiff:
    """Return non-equal line opcodes using zero-based, end-exclusive ranges."""
    before_lines = before.split("\n")
    after_lines = after.split("\n")
    if len(before_lines) + len(after_lines) > MAX_DIFF_LINES:
        return {"truncated": True, "changes": []}

    matcher = SequenceMatcher(a=before_lines, b=after_lines, autojunk=False)
    changes: list[LineChange] = []
    for tag, old_start, old_end, new_start, new_end in matcher.get_opcodes():
        if tag != "equal":
            changes.append(
                {
                    "type": tag,
                    "old_start": old_start,
                    "old_end": old_end,
                    "new_start": new_start,
                    "new_end": new_end,
                }
            )
    return {"truncated": False, "changes": changes}
