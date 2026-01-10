"""Ensure optional third-party stubs are available when dependencies are missing."""
from __future__ import annotations

try:
    from backend._stubs import install as _install_backend_stubs
except ModuleNotFoundError:  # pragma: no cover - backend package absent
    _install_backend_stubs = None

if _install_backend_stubs is not None:
    _install_backend_stubs()
