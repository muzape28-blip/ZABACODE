"""
ZABACODE Plugins — Addon & Marketplace System

Architecture (v1.2.1+): VSCode-inspired contribution pattern.
  - registry.py:          Plugin catalog & marketplace
  - implementations.py:   Plugin implementations (now registered via CommandRegistry)
  - contribution.py:      Decorator-based self-registration (VSCode contrib pattern)
"""
