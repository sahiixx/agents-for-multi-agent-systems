"""Pytest helpers for running the suite without external services."""
from __future__ import annotations

import asyncio
import inspect

import pytest

from tests._stubs import install as install_stubs

# Ensure all lightweight stand-ins are available before any test modules import
# the backend packages.  This mirrors the behaviour of the optional third-party
# dependencies closely enough for unit testing.
install_stubs()


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "asyncio: run test as an asyncio coroutine")


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> bool | None:
    testfunction = pyfuncitem.obj
    if inspect.iscoroutinefunction(testfunction):
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(testfunction(**pyfuncitem.funcargs))
        finally:
            loop.close()
        return True
    return None

