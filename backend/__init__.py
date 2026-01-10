"""Backend package initialisation."""
from __future__ import annotations

try:
    from ._stubs import install as _install_backend_stubs
except ModuleNotFoundError:  # pragma: no cover - dependency missing during packaging
    _install_backend_stubs = None
else:
    _install_backend_stubs()

__all__ = []
