"""
ZABACODE Core — Execution, Security, File Management, Checker, Events, Commands, Services

Architecture inspired by VSCode's layered design:
  - events.py:    EventEmitter + Disposable pattern (from VSCode's base/common/event.ts)
  - commands.py:  Command Registry pattern (from VSCode's platform/commands)
  - services.py:  Service Container / DI (from VSCode's platform/instantiation)
  - Core modules: platform-agnostic business logic (like VSCode's common/ layer)
"""
