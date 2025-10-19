"""Compatibility wrapper to expose backend stub installers to tests."""
from __future__ import annotations

from backend._stubs import install

__all__ = ["install"]
