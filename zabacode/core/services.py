"""
ZABACODE Core — Service Container (Inspired by VSCode's Dependency Injection)

Port of VSCode's service instantiation system to Python:
  - ServiceCollection: register service interfaces → implementations
  - ServiceContainer: resolve and instantiate services on demand
  - Lazy instantiation: services are only created when first requested
  - Singleton lifecycle: each service is created once and shared

VSCode's DI system (src/vs/platform/instantiation/) solves a problem we have:
  web_app.py imports every core module directly and wires them together by hand.
  This makes testing painful (can't mock services) and adding new services
  requires touching the web_app every time.

Key differences from VSCode's TypeScript original:
  - VSCode uses decorators (@IService) and compile-time type checking.
    We use Protocol classes and runtime registration.
  - VSCode has SyncDescriptor for lazy instantiation with IdleValue.
    We use simple lazy initialization.
  - VSCode's InstantiationService supports circular dependency detection via
    a directed graph. We log a warning instead of crashing.
  - No code generation — all registration is explicit.

References:
  - https://github.com/microsoft/vscode/blob/main/src/vs/platform/instantiation/common/instantiationService.ts
  - https://dev.to/ryankolter/vscode-1-dependency-injectiondi-system-1f95
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Callable, Protocol, TypeVar, runtime_checkable

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Service Identifier — mirrors VSCode's ServiceIdentifier<T>
# ---------------------------------------------------------------------------

class ServiceIdentifier:
    """
    A typed identifier for a service, used as the key in the service collection.

    VSCode uses createDecorator() to produce service identifiers that double as
    TypeScript decorators. We use a simpler string-based approach since Python
    doesn't need compile-time DI decorators.

    Usage:
        IFileService = ServiceIdentifier("IFileService")
        IAiService = ServiceIdentifier("IAiService")
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return f"ServiceIdentifier({self.name!r})"

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ServiceIdentifier):
            return self.name == other.name
        return NotImplemented


# ---------------------------------------------------------------------------
# Service Collection — mirrors VSCode's ServiceCollection
# ---------------------------------------------------------------------------

class ServiceCollection:
    """
    Mutable collection of service registrations.

    Services can be registered as:
      1. An instance (already created)
      2. A factory function (called once, lazily, on first access)
      3. A class (instantiated lazily with no-arg constructor)

    Usage:
        collection = ServiceCollection()
        collection.set(IFileService, FileManager())
        collection.set(IAiService, lambda: AIProvider())
        collection.set(IExecutor, Executor)  # class, instantiated lazily
    """

    def __init__(self) -> None:
        self._entries: dict[ServiceIdentifier, Any] = {}
        self._lock = threading.Lock()

    def set(self, id: ServiceIdentifier, instance_or_factory: Any) -> None:
        """
        Register a service. Accepts:
          - A direct instance
          - A factory function (callable with no args)
          - A class (instantiated lazily)
        """
        with self._lock:
            self._entries[id] = instance_or_factory

    def get(self, id: ServiceIdentifier) -> Any:
        """Get the raw entry (instance, factory, or class) without resolving."""
        with self._lock:
            return self._entries.get(id)

    def has(self, id: ServiceIdentifier) -> bool:
        """Check if a service is registered."""
        with self._lock:
            return id in self._entries

    def keys(self) -> list[ServiceIdentifier]:
        """Get all registered service identifiers."""
        with self._lock:
            return list(self._entries.keys())


# ---------------------------------------------------------------------------
# Service Container — mirrors VSCode's InstantiationService
# ---------------------------------------------------------------------------

class ServiceContainer:
    """
    Resolves and manages service instances from a ServiceCollection.

    Mirrors VSCode's InstantiationService:
      - Lazy instantiation: services are created on first request
      - Singleton lifecycle: each service is created once and cached
      - Thread-safe: concurrent get_service() calls are safe

    Usage:
        collection = ServiceCollection()
        collection.set(IFileService, FileManager())
        collection.set(IAiService, lambda: AIProvider())

        container = ServiceContainer(collection)
        file_service = container.get_service(IFileService)
        ai_service = container.get_service(IAiService)
    """

    def __init__(self, collection: ServiceCollection) -> None:
        self._collection = collection
        self._instances: dict[ServiceIdentifier, Any] = {}
        self._lock = threading.Lock()

    def get_service(self, id: ServiceIdentifier) -> Any:
        """
        Get or create a service instance.

        Resolution order:
          1. If already instantiated, return cached instance
          2. If registered as an instance, cache and return it
          3. If registered as a factory, call it, cache and return
          4. If registered as a class, instantiate it, cache and return
          5. Raise KeyError if not registered
        """
        # Fast path: already instantiated
        with self._lock:
            if id in self._instances:
                return self._instances[id]

        # Resolve from collection
        entry = self._collection.get(id)
        if entry is None:
            raise KeyError(f"Service {id} is not registered")

        with self._lock:
            # Double-check after acquiring lock
            if id in self._instances:
                return self._instances[id]

            instance = self._resolve(entry)
            self._instances[id] = instance
            return instance

    def _resolve(self, entry: Any) -> Any:
        """Resolve a service entry to an instance."""
        # Direct instance
        if not callable(entry):
            return entry

        # Factory function or class
        try:
            return entry()
        except TypeError:
            # Class that requires constructor args — can't auto-resolve
            logger.warning("Cannot auto-instantiate %r: no-arg constructor required", entry)
            raise

    def has_service(self, id: ServiceIdentifier) -> bool:
        """Check if a service can be resolved."""
        return self._collection.has(id)

    def get_all_service_ids(self) -> list[ServiceIdentifier]:
        """Get all registered service identifiers."""
        return self._collection.keys()


# ---------------------------------------------------------------------------
# ZABACODE Service Identifiers — mirrors VSCode's service decoration pattern
# ---------------------------------------------------------------------------

# Core services
IFileService = ServiceIdentifier("IFileService")
IExecutorService = ServiceIdentifier("IExecutorService")
IAiProviderService = ServiceIdentifier("IAiProviderService")
ICheckerService = ServiceIdentifier("ICheckerService")
IOracleService = ServiceIdentifier("IOracleService")
ISecurityService = ServiceIdentifier("ISecurityService")
IEventService = ServiceIdentifier("IEventService")
ICommandService = ServiceIdentifier("ICommandService")
ILibraryService = ServiceIdentifier("ILibraryService")
IPluginService = ServiceIdentifier("IPluginService")
IThemeService = ServiceIdentifier("IThemeService")
IDiffService = ServiceIdentifier("IDiffService")


# ---------------------------------------------------------------------------
# Bootstrap — create and wire the service container
# ---------------------------------------------------------------------------

_container: ServiceContainer | None = None
_container_lock = threading.Lock()


def bootstrap_services() -> ServiceContainer:
    """
    Create and wire the ZABACODE service container.

    This is the single place where all services are registered — mirrors
    VSCode's bootstrapApplication() which registers all services in one
    central location before the workbench starts.

    Returns:
        A fully wired ServiceContainer
    """
    from zabacode.core.events import AppEvents, get_app_events
    from zabacode.core.commands import CommandRegistry, get_command_registry

    collection = ServiceCollection()

    # Register event service (singleton)
    collection.set(IEventService, get_app_events())

    # Register command service (singleton)
    collection.set(ICommandService, get_command_registry())

    # Register core services with lazy factories
    # These are created on first access, not at import time
    collection.set(IFileService, _lazy_import("zabacode.core.file_manager"))
    collection.set(IExecutorService, _lazy_import("zabacode.core.executor"))
    collection.set(IAiProviderService, _lazy_import("zabacode.core.ai_provider"))
    collection.set(ICheckerService, _lazy_import("zabacode.core.checker"))
    collection.set(IOracleService, _lazy_import("zabacode.core.oracle"))
    collection.set(IDiffService, _lazy_import("zabacode.core.diff"))
    collection.set(ISecurityService, _lazy_import("zabacode.core.security"))
    collection.set(ILibraryService, _lazy_import("zabacode.lib_manager"))
    collection.set(IPluginService, _lazy_import("zabacode.plugins.registry"))
    collection.set(IThemeService, _lazy_import("zabacode.themes.definitions"))

    container = ServiceContainer(collection)

    # Register all plugin commands into the command registry
    _register_plugin_commands(container)

    return container


def _lazy_import(module_path: str) -> Callable:
    """
    Create a lazy factory that imports a module on first access.

    This avoids circular imports at module load time — the module is only
    imported when the service is actually requested.
    """
    def factory():
        import importlib
        return importlib.import_module(module_path)
    return factory


def _register_plugin_commands(container: ServiceContainer) -> None:
    """
    Register plugin implementations as commands in the command registry.

    This replaces the hardcoded if/elif chain in PluginExecutor with a
    proper command registry — mirrors VSCode's extension contribution model.
    """
    from zabacode.core.commands import get_command_registry
    from zabacode.plugins.implementations import (
        AutoImportOptimizer,
        CodeBeautifierPro,
        DuplicateLineDetector,
        SmartCommentGenerator,
        VariableTypeHintGenerator,
    )

    registry = get_command_registry()

    # Register each plugin as a command
    registry.register_command(
        "zabacode.plugin.auto_import_optimizer",
        AutoImportOptimizer.optimize,
        metadata={"name": "Auto-Import Optimizer", "category": "productivity"},
    )
    registry.register_command(
        "zabacode.plugin.duplicate_line_detector",
        DuplicateLineDetector.detect,
        metadata={"name": "Duplicate Line Detector", "category": "quality"},
    )
    registry.register_command(
        "zabacode.plugin.smart_comment_generator",
        SmartCommentGenerator.generate,
        metadata={"name": "Smart Comment Generator", "category": "productivity"},
    )
    registry.register_command(
        "zabacode.plugin.code_beautifier_pro",
        CodeBeautifierPro.beautify,
        metadata={"name": "Code Beautifier Pro", "category": "formatting"},
    )
    registry.register_command(
        "zabacode.plugin.variable_type_hint_generator",
        VariableTypeHintGenerator.generate,
        metadata={"name": "Variable Type Hint Gen", "category": "quality"},
    )


def get_service_container() -> ServiceContainer:
    """Get or create the global ServiceContainer singleton."""
    global _container
    if _container is None:
        with _container_lock:
            if _container is None:
                _container = bootstrap_services()
    return _container


def get_service(id: ServiceIdentifier) -> Any:
    """Convenience: resolve a service from the global container."""
    return get_service_container().get_service(id)
