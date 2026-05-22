"""Pytest configuration for the test suite."""
import pytest


# Use anyio as the async backend (it's installed; pytest-asyncio is not)
@pytest.fixture
def anyio_backend():
    return "asyncio"
