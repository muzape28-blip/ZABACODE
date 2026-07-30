"""
ZABACODE Core — Event System (Inspired by VSCode's EventEmitter + IDisposable)

Port of VSCode's event architecture to Python:
  - Emitter<T>: manages listeners and fires events
  - Disposable: automatic resource cleanup via _register() / dispose()
  - Event<T>: typed event subscription that returns a Disposable

VSCode's design solved three problems we also have:
  1. Tight coupling between web_app routes and core modules
  2. No way for plugins to react to lifecycle events (code run, file save, etc.)
  3. Resource leaks when listeners are never removed

Key differences from the TypeScript original:
  - Python has no structural typing, so we use Protocols for type safety
  - Thread safety added via threading.Lock (VSCode is single-threaded in the renderer)
  - fire() catches exceptions per listener so one bad handler doesn't kill the rest

References:
  - https://github.com/microsoft/vscode/blob/main/src/vs/base/common/event.ts
  - https://dev.to/ryankolter/vscode-3-event-system-from-emitters-to-disposables-3292
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Callable, Generic, Protocol, TypeVar, runtime_checkable

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ---------------------------------------------------------------------------
# IDisposable — mirror of VSCode's base lifecycle interface
# ---------------------------------------------------------------------------

@runtime_checkable
class IDisposable(Protocol):
    """Protocol for resources that need cleanup."""

    def dispose(self) -> None: ...


class Disposable:
    """
    Base class that tracks disposable resources and cleans them up on dispose().

    VSCode's Disposable uses a Set<IDisposable>; we use a list with a lock
    because Python's Set is not thread-safe for concurrent add/dispose.

    Usage (mirrors VSCode's _register pattern):
        class MyService(Disposable):
            def __init__(self):
                super().__init__()
                self._register(some_emitter.event(self.on_something))
    """

    def __init__(self) -> None:
        self._disposables: list[IDisposable] = []
        self._lock = threading.Lock()
        self._disposed = False

    def _register(self, disposable: IDisposable) -> IDisposable:
        """Register a disposable for automatic cleanup. Returns it for chaining."""
        with self._lock:
            if self._disposed:
                disposable.dispose()
                return disposable
            self._disposables.append(disposable)
        return disposable

    def dispose(self) -> None:
        """Dispose all registered disposables in reverse order (LIFO)."""
        with self._lock:
            self._disposed = True
            # LIFO: last registered is disposed first, matching VSCode's behavior
            while self._disposables:
                d = self._disposables.pop()
                try:
                    d.dispose()
                except Exception:
                    logger.debug("Error disposing %r", d, exc_info=True)


class DisposableStore:
    """
    Safe alternative to IDisposable[] — mirrors VSCode's DisposableStore.

    VSCode issue #74250: raw IDisposable[] is unsafe because a dispose()
    followed by a push() silently leaks. DisposableStore guards against this.

    Usage:
        store = DisposableStore()
        store.add(emitter.event(handler))
        store.dispose()  # all added disposables are cleaned up
    """

    def __init__(self) -> None:
        self._toDispose: list[IDisposable] = []
        self._lock = threading.Lock()
        self._disposed = False

    def add(self, disposable: IDisposable) -> IDisposable:
        """Add a disposable. If already disposed, dispose immediately."""
        with self._lock:
            if self._disposed:
                disposable.dispose()
                return disposable
            self._toDispose.append(disposable)
        return disposable

    def dispose(self) -> None:
        """Dispose all and prevent future additions."""
        with self._lock:
            self._disposed = True
            while self._toDispose:
                d = self._toDispose.pop()
                try:
                    d.dispose()
                except Exception:
                    logger.debug("Error disposing %r", d, exc_info=True)


# ---------------------------------------------------------------------------
# Emitter<T> — port of VSCode's Emitter class
# ---------------------------------------------------------------------------

class Emitter(Generic[T]):
    """
    An event emitter that manages listeners and fires events.

    Direct port of VSCode's Emitter<T> with Python-specific adaptations:
      - Thread-safe listener management (VSCode renderer is single-threaded)
      - Exception isolation: one bad listener doesn't prevent others from running
      - Optional onWillAddFirstListener / onDidRemoveLastListener hooks
        (VSCode uses these for lazy subscription wiring)

    Usage:
        class FileService:
            def __init__(self):
                self._onDidSave = Emitter[dict]()
                self.onDidSave = self._onDidSave.event  # expose only the event

            def save(self, filename, content):
                # ... save logic ...
                self._onDidSave.fire({"filename": filename, "content": content})

        # Consumer
        service = FileService()
        disposable = service.onDidSave(lambda e: print(f"Saved {e['filename']}"))
        # Later:
        disposable.dispose()  # unsubscribe
    """

    def __init__(
        self,
        *,
        on_will_add_first_listener: Callable[[], None] | None = None,
        on_did_remove_last_listener: Callable[[], None] | None = None,
    ) -> None:
        self._listeners: list[Callable[[T], Any]] = []
        self._lock = threading.Lock()
        self._on_will_add_first = on_will_add_first_listener
        self._on_did_remove_last = on_did_remove_last_listener
        self._disposed = False

    @property
    def event(self) -> Callable[[Callable[[T], Any]], IDisposable]:
        """
        The event function — subscribe by calling it with a listener.

        Returns a Disposable that unsubscribes when disposed.
        This mirrors VSCode's `readonly event` property.
        """
        def subscribe(listener: Callable[[T], Any]) -> IDisposable:
            with self._lock:
                if self._disposed:
                    return _NOOP_DISPOSABLE
                is_first = len(self._listeners) == 0
                self._listeners.append(listener)

            if is_first and self._on_will_add_first:
                self._on_will_add_first()

            disposed = False

            def unsubscribe() -> None:
                nonlocal disposed
                if disposed:
                    return
                disposed = True
                with self._lock:
                    try:
                        self._listeners.remove(listener)
                    except ValueError:
                        pass
                    is_last = len(self._listeners) == 0
                if is_last and self._on_did_remove_last:
                    self._on_did_remove_last()

            return _make_disposable(unsubscribe)

        return subscribe

    def fire(self, data: T) -> None:
        """
        Notify all listeners. Exceptions in one listener don't affect others.

        VSCode fires a snapshot copy of listeners to handle listeners that
        remove themselves during the callback. We do the same.
        """
        with self._lock:
            if self._disposed:
                return
            listeners = list(self._listeners)

        for listener in listeners:
            try:
                listener(data)
            except Exception:
                logger.debug("Error in event listener %r", listener, exc_info=True)

    def dispose(self) -> None:
        """Dispose the emitter and remove all listeners."""
        with self._lock:
            self._disposed = True
            self._listeners.clear()
        if self._on_did_remove_last:
            self._on_did_remove_last()

    @property
    def listener_count(self) -> int:
        """Number of active listeners (for debugging/metrics)."""
        with self._lock:
            return len(self._listeners)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _NoopDisposable:
    """A disposable that does nothing — mirrors VSCode's Disposable.None."""

    def dispose(self) -> None:
        pass


_NOOP_DISPOSABLE = _NoopDisposable()


def _make_disposable(dispose_fn: Callable[[], None]) -> IDisposable:
    """Create an IDisposable from a simple function."""
    class _FnDisposable:
        def dispose(self) -> None:
            dispose_fn()
    return _FnDisposable()


# ---------------------------------------------------------------------------
# Event utility functions — mirrors VSCode's Event namespace helpers
# ---------------------------------------------------------------------------

def event_any(*events: Callable[[Callable[[Any], Any]], IDisposable]) -> Callable[[Callable[[Any], Any]], IDisposable]:
    """
    Combine multiple events into one. Fires when any source fires.

    Mirrors VSCode's Event.any().
    Usage:
        combined = event_any(service.onDidSave, service.onDidDelete)
        disposable = combined(lambda e: print("File changed!"))
    """
    def subscribe(listener: Callable[[Any], Any]) -> IDisposable:
        store = DisposableStore()
        for evt in events:
            store.add(evt(listener))
        return store

    return subscribe


def debounce_event(
    event: Callable[[Callable[[T], Any]], IDisposable],
    delay: float,
) -> Callable[[Callable[[T], Any]], IDisposable]:
    """
    Debounce an event — only fire after `delay` seconds of silence.

    Mirrors VSCode's Event.debounce().
    Useful for rapid-fire events like keystrokes or file changes.
    """
    import time

    def subscribe(listener: Callable[[T], Any]) -> IDisposable:
        last_data: list[T | None] = [None]
        timer: list[threading.Timer | None] = [None]

        def on_event(data: T) -> None:
            last_data[0] = data
            if timer[0] is not None:
                timer[0].cancel()
            timer[0] = threading.Timer(delay, lambda: listener(last_data[0]))  # type: ignore[arg-type]
            timer[0].daemon = True
            timer[0].start()

        def dispose() -> None:
            if timer[0] is not None:
                timer[0].cancel()

        inner = event(on_event)
        return _make_disposable(lambda: (dispose(), inner.dispose()))

    return subscribe


# ---------------------------------------------------------------------------
# ZABACODE Application Events — typed event contracts
# ---------------------------------------------------------------------------

class AppEvents(Disposable):
    """
    Central event bus for ZABACODE — inspired by VSCode's workbench event model.

    VSCode exposes events on individual services (e.g. IFileService.onDidSave),
    but also has a central event bus for cross-cutting concerns. We do both:
    services own their own emitters, and AppEvents provides a global bus for
    plugins and cross-cutting concerns.

    Events are named onDidSomething / onWillSomething, matching VSCode convention:
      - onWill* = before the action (can be cancelled in future)
      - onDid*  = after the action completed
    """

    def __init__(self) -> None:
        super().__init__()
        # --- Code Execution Events ---
        self._onWillRunCode = Emitter[dict]()
        self.onWillRunCode = self._onWillRunCode.event
        self._register(self._onWillRunCode)

        self._onDidRunCode = Emitter[dict]()
        self.onDidRunCode = self._onDidRunCode.event
        self._register(self._onDidRunCode)

        # --- File Events ---
        self._onDidSaveFile = Emitter[dict]()
        self.onDidSaveFile = self._onDidSaveFile.event
        self._register(self._onDidSaveFile)

        self._onDidDeleteFile = Emitter[dict]()
        self.onDidDeleteFile = self._onDidDeleteFile.event
        self._register(self._onDidDeleteFile)

        # --- AI Chat Events ---
        self._onWillAIChat = Emitter[dict]()
        self.onWillAIChat = self._onWillAIChat.event
        self._register(self._onWillAIChat)

        self._onDidAIChat = Emitter[dict]()
        self.onDidAIChat = self._onDidAIChat.event
        self._register(self._onDidAIChat)

        # --- Plugin Events ---
        self._onDidTogglePlugin = Emitter[dict]()
        self.onDidTogglePlugin = self._onDidTogglePlugin.event
        self._register(self._onDidTogglePlugin)

        # --- Library Events ---
        self._onDidInstallLibrary = Emitter[dict]()
        self.onDidInstallLibrary = self._onDidInstallLibrary.event
        self._register(self._onDidInstallLibrary)

    # Convenience methods for firing events from core modules
    def fire_will_run_code(self, data: dict) -> None:
        self._onWillRunCode.fire(data)

    def fire_did_run_code(self, data: dict) -> None:
        self._onDidRunCode.fire(data)

    def fire_did_save_file(self, data: dict) -> None:
        self._onDidSaveFile.fire(data)

    def fire_did_delete_file(self, data: dict) -> None:
        self._onDidDeleteFile.fire(data)

    def fire_will_ai_chat(self, data: dict) -> None:
        self._onWillAIChat.fire(data)

    def fire_did_ai_chat(self, data: dict) -> None:
        self._onDidAIChat.fire(data)

    def fire_did_toggle_plugin(self, data: dict) -> None:
        self._onDidTogglePlugin.fire(data)

    def fire_did_install_library(self, data: dict) -> None:
        self._onDidInstallLibrary.fire(data)


# Singleton instance — created once and shared across the application
_app_events: AppEvents | None = None
_events_lock = threading.Lock()


def get_app_events() -> AppEvents:
    """Get or create the global AppEvents singleton."""
    global _app_events
    if _app_events is None:
        with _events_lock:
            if _app_events is None:
                _app_events = AppEvents()
    return _app_events
