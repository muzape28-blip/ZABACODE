"""
ZABACODE Plugins — Contribution System (Inspired by VSCode's workbench/contrib pattern)

VSCode's workbench contributions live in vs/workbench/contrib/<feature>/
Each feature has a single .contribution.ts file that self-registers into the
workbench. This is the Python equivalent: plugins import this module and
use decorators to register themselves as commands and event listeners.

Usage:
    from zabacode.plugins.contribution import plugin_command, on_event

    @plugin_command("zabacode.plugin.my_cool_plugin")
    def my_plugin_handler(code: str) -> tuple[str, list[str]]:
        # ... transform code ...
        return new_code, ["Report line 1"]

    @on_event("onDidRunCode")
    def on_code_run(data: dict) -> None:
        print(f"Code ran: {data}")

When this module is imported, all decorated functions are automatically
registered into the global command registry and event bus.
"""

from __future__ import annotations

from typing import Any, Callable

from zabacode.core.commands import get_command_registry
from zabacode.core.events import get_app_events


def plugin_command(
    command_id: str,
    *,
    metadata: dict[str, Any] | None = None,
) -> Callable:
    """
    Decorator to register a function as a plugin command.

    Mirrors VSCode's registerCommand() pattern:
      - Each plugin self-registers instead of being hardcoded
      - The command registry is the single source of truth
      - New plugins can be added without touching core code

    Usage:
        @plugin_command("zabacode.plugin.my_cool_plugin")
        def my_handler(code: str) -> tuple[str, list[str]]:
            return code, ["No changes needed"]
    """
    def decorator(func: Callable) -> Callable:
        registry = get_command_registry()
        registry.register_command(command_id, func, metadata=metadata)
        return func
    return decorator


def on_event(event_name: str) -> Callable:
    """
    Decorator to subscribe to an application event.

    Mirrors VSCode's event subscription pattern:
      - Listeners are registered declaratively
      - The disposable is tracked for cleanup

    Supported event names:
      - "onWillRunCode"    — before code execution starts
      - "onDidRunCode"     — after code execution completes
      - "onDidSaveFile"    — after a file is saved
      - "onDidDeleteFile"  — after a file is deleted
      - "onWillAIChat"     — before AI chat request
      - "onDidAIChat"      — after AI chat response
      - "onDidTogglePlugin" — after a plugin is toggled
      - "onDidInstallLibrary" — after a library is installed

    Usage:
        @on_event("onDidRunCode")
        def on_code_run(data: dict) -> None:
            print(f"Code ran: {data}")
    """
    def decorator(func: Callable) -> Callable:
        events = get_app_events()
        event_map = {
            "onWillRunCode": events.onWillRunCode,
            "onDidRunCode": events.onDidRunCode,
            "onDidSaveFile": events.onDidSaveFile,
            "onDidDeleteFile": events.onDidDeleteFile,
            "onWillAIChat": events.onWillAIChat,
            "onDidAIChat": events.onDidAIChat,
            "onDidTogglePlugin": events.onDidTogglePlugin,
            "onDidInstallLibrary": events.onDidInstallLibrary,
        }
        event_fn = event_map.get(event_name)
        if event_fn is None:
            raise ValueError(
                f"Unknown event '{event_name}'. "
                f"Available: {', '.join(sorted(event_map.keys()))}"
            )
        # Subscribe and register the disposable for cleanup
        events._register(event_fn(func))
        return func
    return decorator
