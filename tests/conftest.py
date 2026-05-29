"""
pytest configuration for laziest-import tests.
"""

import pytest
import asyncio

pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.get_event_loop_policy()
