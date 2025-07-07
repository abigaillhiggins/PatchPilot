# db_utils.py
# Placeholder content for db_utils.py
# This would typically handle database connections and operations

import sqlite3
import os
import logging
import threading
from typing import List, Optional
from models import TodoItem

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database operations for AutoCodeRover."""
    
    def __init__(self, db_path: str):
        """Initialize database connection and create tables if they don't exist."""
        self.db_path = db_path
        self._local = threading.local()
        self._create_tables()

    @property
    def conn(self) -> sqlite3.Connection:
        """Get a thread-local database connection."""
        if not hasattr(self._local, 'conn'):
            if self.db_path == ":memory:":
                # For in-memory database, we need to recreate tables for each thread
                self._local.conn = self._connect()
                self._create_tables_for_conn(self._local.conn)
            else:
                self._local.conn = self._connect()
        return self._local.conn

    def _connect(self) -> sqlite3.Connection:
        """Create a database connection."""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {str(e)}")
            raise

    def _create_tables_for_conn(self, conn: sqlite3.Connection) -> None:
        """Create necessary database tables for a specific connection."""
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS todos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    completed BOOLEAN DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error creating tables: {str(e)}")
            raise

    def _create_tables(self) -> None:
        """Create necessary database tables if they don't exist."""
        self._create_tables_for_conn(self.conn)

    def add_todo(self, todo: TodoItem) -> bool:
        """Add a new todo item to the database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO todos (title, description, completed, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (todo.title, todo.description, todo.completed, todo.created_at)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding todo: {str(e)}")
            return False

    def get_todos(self) -> List[TodoItem]:
        """Get all todo items from the database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM todos ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [
                TodoItem(
                    id=row['id'],
                    title=row['title'],
                    description=row['description'],
                    completed=bool(row['completed']),
                    created_at=row['created_at']
                )
                for row in rows
            ]
        except sqlite3.Error as e:
            logger.error(f"Error getting todos: {str(e)}")
            return []

    def fix_permissions(self) -> bool:
        """Fix database file permissions."""
        try:
            if os.path.exists(self.db_path) and self.db_path != ":memory:":
                os.chmod(self.db_path, 0o666)
                return True
            return False
        except Exception as e:
            logger.error(f"Error fixing permissions: {str(e)}")
            return False

    def repair_corruption(self) -> bool:
        """Attempt to repair database corruption."""
        try:
            # Basic corruption check and repair
            cursor = self.conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            
            if result and result[0] == "ok":
                return True
            
            # If corruption detected, try to recover
            cursor.execute("VACUUM")
            self.conn.commit()
            
            # Verify repair
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            return result and result[0] == "ok"
            
        except sqlite3.Error as e:
            logger.error(f"Error repairing corruption: {str(e)}")
            return False

    def close(self) -> None:
        """Close the database connection."""
        try:
            if hasattr(self._local, 'conn'):
                self._local.conn.close()
                del self._local.conn
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}")

    def __del__(self):
        """Ensure connections are closed on object deletion."""
        self.close()

# Add more utility functions as needed