"""
This module defines the base Table class for SQLite database operations.

The Table class provides a common interface for creating, reading, updating, and deleting
records in SQLite tables, as well as support for schema migrations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Type, TypeVar, Generic

import aiosqlite
from pydantic import BaseModel

from assistants.config.file_management import DB_PATH

T = TypeVar("T", bound=BaseModel)


class Table(Generic[T], ABC):
    """
    Base class for SQLite table operations.

    This class provides a common interface for CRUD operations on SQLite tables
    and supports schema migrations.

    Attributes:
        db_path (str): Path to the SQLite database file
        table_name (str): Name of the table
        model_class (Type[T]): Pydantic model class for the table records
    """

    DB_PATH: str = DB_PATH  # Default database path

    def __init__(self, db_path: Optional[str] = None) -> None:
        """
        Initialize the Table instance.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path or self.DB_PATH
        self.table_name = self.get_table_name()
        self.model_class = self.get_model_class()

    @abstractmethod
    def get_table_name(self) -> str:
        """
        Get the name of the table.

        Returns:
            The name of the table
        """
        pass

    @abstractmethod
    def get_model_class(self) -> Type[T]:
        """
        Get the Pydantic model class for the table records.

        Returns:
            The Pydantic model class
        """
        pass

    @abstractmethod
    def get_create_table_sql(self) -> str:
        """
        Get the SQL statement for creating the table.

        Returns:
            The SQL CREATE TABLE statement
        """
        pass

    async def create_table(self) -> None:
        """
        Create the table if it doesn't exist.
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(self.get_create_table_sql())
            await db.commit()

    async def drop_table(self) -> None:
        """
        Drop the table if it exists.
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"DROP TABLE IF EXISTS {self.table_name};")
            await db.commit()

    async def table_exists(self) -> bool:
        """
        Check if the table exists.

        Returns:
            True if the table exists, False otherwise
        """
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
                (self.table_name,),
            ) as cursor:
                result = await cursor.fetchone()
                return result is not None

    @abstractmethod
    async def migrate_if_needed(self) -> None:
        """
        Perform schema migrations if needed.

        This method should check the current schema and perform migrations
        if the schema has changed.
        """
        pass

    @abstractmethod
    async def insert(self, record: T) -> None:
        """
        Insert a record into the table.

        Args:
            record: The record to insert
        """
        pass

    @abstractmethod
    async def update(self, record: T) -> None:
        """
        Update a record in the table.

        Args:
            record: The record to update
        """
        pass

    @abstractmethod
    async def delete(self, **kwargs) -> None:
        """
        Delete a record from the table.

        Args:
            **kwargs: Key-value pairs for identifying the record to delete
        """
        pass

    @abstractmethod
    async def get(self, **kwargs) -> Optional[T]:
        """
        Get a record from the table.

        Args:
            **kwargs: Key-value pairs for identifying the record to get

        Returns:
            The record if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_all(self) -> List[T]:
        """
        Get all records from the table.

        Returns:
            A list of all records
        """
        pass
