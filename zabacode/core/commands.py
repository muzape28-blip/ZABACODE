"""
ZABACODE Core — Command Registry (Inspired by VSCode's CommandsRegistry)

Port of VSCode's command system to Python:
  - register_command(id, handler): register a named command
  - execute_command(id, *args): execute a command by ID
  - Decorator syntax: @command("my.id")

VSCode's CommandsRegistry solves a problem we have:
  PluginExecutor.execute_plugin() is a hardcoded if/elif chain that must be
  edited every time a new plugin is added. The command pattern makes it
  extensible — plugins self-register without touching core code.

Key differences from VSCode's TypeScript original:
  - VSCode uses LinkedList for per-ID command stacks (override support).
    We use a simple dict since Python plugins don't need override chains.
  - VSCode's commands have keybinding and menu integration; ours are
    backend-only (the WebView UI calls them via API).
  - Thread safety added via threading.Lock.

References:
  - https://github.com/microsoft/vscode/blob/main/src/vs/platform/commands/common/commands.ts
  - https://dev.to/ryankolter/vscode-4-commands-and-keybindings-system-4nhm
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Callable

from zabacode.core.events import IDisposable, _make_disposable

logger = logging.getLogger(__name__)

# Type alias for command handlers
CommandHandler = Callable[..., Any]


class CommandRegistry:
    """
    Central registry for named commands — mirrors VSCode's CommandsRegistry.

    Commands are identified by string IDs (e.g. "zabacode.plugin.auto_import").
    Each command has a handler function. Registering a command returns a
    Disposable that unregisters it when disposed.

    Usage:
        registry = CommandRegistry()

        # Functional registration
        disposable = registry.register_command("myApp.doSomething", lambda x: x * 2)

        # Decorator registration
        @registry.command("myApp.doSomething")
        def do_something(x):
            return x * 2

        # Execution
        result = registry.execute_command("myApp.doSomething", 21)
        # result == 42

        # Cleanup
        disposable.dispose()
    """

    def __init__(self) -> None:
        self._commands: dict[str, CommandHandler] = {}
        self._metadata: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def register_command(
        self,
        id: str,
        handler: CommandHandler,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> IDisposable:
        """
        Register a command with a handler function.

        Args:
            id: Unique command identifier (e.g. "zabacode.plugin.auto_import")
            handler: Function to execute when the command is invoked
            metadata: Optional metadata (description, category, etc.)

        Returns:
            IDisposable that unregisters the command when disposed.
        """
        with self._lock:
            if id in self._commands:
                logger.warning("Command '%s' is already registered, overwriting", id)
            self._commands[id] = handler
            if metadata:
                self._metadata[id] = metadata

        def unregister() -> None:
            with self._lock:
                self._commands.pop(id, None)
                self._metadata.pop(id, None)

        return _make_disposable(unregister)

    def command(self, id: str, *, metadata: dict[str, Any] | None = None):
        """
        Decorator to register a command.

        Usage:
            registry = CommandRegistry()

            @registry.command("zabacode.greet")
            def greet(name: str) -> str:
                return f"Hello, {name}!"
        """
        def decorator(func: CommandHandler) -> CommandHandler:
            self.register_command(id, func, metadata=metadata)
            return func
        return decorator

    def execute_command(self, id: str, *args: Any, **kwargs: Any) -> Any:
        """
        Execute a registered command by ID.

        Args:
            id: The command identifier
            *args: Positional arguments for the handler
            **kwargs: Keyword arguments for the handler

        Returns:
            The return value of the command handler

        Raises:
            KeyError: If the command is not registered
        """
        with self._lock:
            handler = self._commands.get(id)

        if handler is None:
            raise KeyError(f"Command '{id}' is not registered")

        return handler(*args, **kwargs)

    def has_command(self, id: str) -> bool:
        """Check if a command is registered."""
        with self._lock:
            return id in self._commands

    def get_command_ids(self) -> list[str]:
        """Get all registered command IDs."""
        with self._lock:
            return list(self._commands.keys())

    def get_command_metadata(self, id: str) -> dict[str, Any] | None:
        """Get metadata for a command, or None if not registered."""
        with self._lock:
            return self._metadata.get(id)

    def get_all_commands_info(self) -> dict[str, dict[str, Any]]:
        """Get info about all registered commands (for UI/debugging)."""
        with self._lock:
            result = {}
            for id in self._commands:
                info: dict[str, Any] = {"id": id}
                if id in self._metadata:
                    info["metadata"] = self._metadata[id]
                result[id] = info
            return result


# ---------------------------------------------------------------------------
# Global singleton — mirrors VSCode's static CommandsRegistry
# ---------------------------------------------------------------------------

_registry: CommandRegistry | None = None
_registry_lock = threading.Lock()


def get_command_registry() -> CommandRegistry:
    """Get or create the global CommandRegistry singleton."""
    global _registry
    if _registry is None:
        with _registry_lock:
            if _registry is None:
                _registry = CommandRegistry()
    return _registry


def register_command(id: str, handler: CommandHandler, **kwargs) -> IDisposable:
    """Convenience: register a command on the global registry."""
    return get_command_registry().register_command(id, handler, **kwargs)


def execute_command(id: str, *args: Any, **kwargs: Any) -> Any:
    """Convenience: execute a command on the global registry."""
    return get_command_registry().execute_command(id, *args, **kwargs)
