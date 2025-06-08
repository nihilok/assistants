"""
This module contains pytest fixtures for the assistants tests.
"""

import asyncio
import os
import pytest
import tempfile

from assistants.user_data.sqlite_backend import init_db
from assistants.user_data.sqlite_backend.table import Table
from assistants.user_data.sqlite_backend.telegram_chat_data import (
    TelegramSqliteUserData,
)


@pytest.fixture(scope="session", autouse=True)
def patch_db_path():
    """
    Patch Table.DB_PATH to use a temporary database file for tests.

    This fixture runs automatically for all tests and ensures that tests
    use a separate database file instead of the production database.
    """
    # Create a temporary directory for the test database
    test_db_dir = tempfile.mkdtemp()
    test_db_path = os.path.join(test_db_dir, "test_db.sqlite")

    # Store the original DB_PATH
    original_db_path = Table.DB_PATH

    # Patch Table.DB_PATH to use the test database
    Table.DB_PATH = test_db_path
    TelegramSqliteUserData.DB = test_db_path

    asyncio.run(init_db())

    # Run the tests
    yield

    # Clean up: restore the original DB_PATH
    Table.DB_PATH = original_db_path
    TelegramSqliteUserData.DB = original_db_path

    # Remove the temporary database file if it exists
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    # Remove the temporary directory
    os.rmdir(test_db_dir)
