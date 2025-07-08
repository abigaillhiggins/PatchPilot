# db_utils.py
# Placeholder content for db_utils.py
# This would typically handle database connections and operations

import sqlite3
import os
import logging
import threading
import json
from typing import List, Optional
from src.core.models import TodoItem
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database operations for PatchPilot."""
    
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
            
            # Create todos table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS todos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    completed BOOLEAN DEFAULT 0,
                    created_at TEXT NOT NULL,
                    language TEXT,
                    requirements TEXT,
                    package_requirements TEXT,
                    context TEXT,
                    metadata TEXT,
                    patch_id TEXT
                )
            """)

            # Create learning_history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_type TEXT NOT NULL,
                    context JSON NOT NULL,
                    decision TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)

            # Create error_solutions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS error_solutions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_pattern TEXT NOT NULL,
                    solution TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    timestamp TEXT NOT NULL,
                    UNIQUE(error_pattern, solution)
                )
            """)

            # Create metrics_history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    name TEXT NOT NULL,
                    value REAL NOT NULL,
                    timestamp TEXT NOT NULL
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
            values = (
                todo.title,
                todo.description,
                todo.completed,
                todo.created_at,
                todo.language,
                json.dumps(todo.requirements) if todo.requirements else None,
                json.dumps(todo.package_requirements) if todo.package_requirements else None,
                todo.context,
                json.dumps(todo.metadata) if todo.metadata else None,
                todo.patch_id
            )
            logger.debug(f"Inserting todo with values: {values}")
            try:
                cursor.execute(
                    """
                    INSERT INTO todos (
                        title, description, completed, created_at,
                        language, requirements, package_requirements,
                        context, metadata, patch_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    values
                )
            except sqlite3.Error as e:
                logger.error(f"SQL Error: {str(e)}")
                logger.error(f"SQL State: {e.sqlite_errorcode}")
                logger.error(f"SQL Message: {e.sqlite_errorname}")
                raise
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Database Error: {str(e)}")
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
                    created_at=row['created_at'],
                    language=row['language'],
                    requirements=json.loads(row['requirements']) if row['requirements'] else [],
                    package_requirements=json.loads(row['package_requirements']) if row['package_requirements'] else [],
                    context=row['context'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {},
                    patch_id=row['patch_id']
                )
                for row in rows
            ]
        except sqlite3.Error as e:
            logger.error(f"Error getting todos: {str(e)}")
            return []

    def update_todo_patch_id(self, todo_id: int, patch_id: str) -> bool:
        """Update the patch_id for a todo item."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE todos SET patch_id = ? WHERE id = ?",
                (patch_id, todo_id)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating todo patch_id: {str(e)}")
            return False

    def get_todo_by_id(self, todo_id: int) -> Optional[TodoItem]:
        """Get a todo item by its ID."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
            row = cursor.fetchone()
            if row:
                return TodoItem(
                    id=row['id'],
                    title=row['title'],
                    description=row['description'],
                    completed=bool(row['completed']),
                    created_at=row['created_at'],
                    language=row['language'],
                    requirements=json.loads(row['requirements']) if row['requirements'] else [],
                    package_requirements=json.loads(row['package_requirements']) if row['package_requirements'] else [],
                    context=row['context'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {},
                    patch_id=row['patch_id']
                )
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting todo by ID: {str(e)}")
            return None

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

    def save_decision(self, decision_type: str, context: dict, decision: str, outcome: str) -> bool:
        """Save a decision outcome to the learning history."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO learning_history (
                    decision_type, context, decision, outcome, timestamp
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    decision_type,
                    json.dumps(context),
                    decision,
                    outcome,
                    datetime.now().isoformat()
                )
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error saving decision: {str(e)}")
            return False

    def save_error_solution(self, error_pattern: str, solution: str, success: bool) -> bool:
        """Save an error solution attempt."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO error_solutions (
                    error_pattern, solution, success, timestamp
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    error_pattern,
                    solution,
                    success,
                    datetime.now().isoformat()
                )
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error saving error solution: {str(e)}")
            return False

    def save_metric(self, category: str, name: str, value: float) -> bool:
        """Save a metric data point."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO metrics_history (
                    category, name, value, timestamp
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    category,
                    name,
                    value,
                    datetime.now().isoformat()
                )
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error saving metric: {str(e)}")
            return False

    def get_similar_decisions(self, decision_type: str, context: dict, limit: int = 5) -> List[dict]:
        """Get similar past decisions based on type and context."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT * FROM learning_history
                WHERE decision_type = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (decision_type, limit)
            )
            rows = cursor.fetchall()
            return [
                {
                    'decision_type': row['decision_type'],
                    'context': json.loads(row['context']),
                    'decision': row['decision'],
                    'outcome': row['outcome'],
                    'timestamp': row['timestamp']
                }
                for row in rows
            ]
        except sqlite3.Error as e:
            logger.error(f"Error getting similar decisions: {str(e)}")
            return []

    def get_best_error_solution(self, error_pattern: str) -> Optional[str]:
        """Get the most successful solution for an error pattern."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT solution
                FROM error_solutions
                WHERE error_pattern = ? AND success = 1
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (error_pattern,)
            )
            row = cursor.fetchone()
            return row['solution'] if row else None
        except sqlite3.Error as e:
            logger.error(f"Error getting best error solution: {str(e)}")
            return None

    def get_metric_history(self, category: str, name: str, hours: int = 24) -> List[dict]:
        """Get metric history for a specific period."""
        try:
            cursor = self.conn.cursor()
            time_threshold = (datetime.now() - timedelta(hours=hours)).isoformat()
            cursor.execute(
                """
                SELECT * FROM metrics_history
                WHERE category = ? AND name = ? AND timestamp > ?
                ORDER BY timestamp ASC
                """,
                (category, name, time_threshold)
            )
            rows = cursor.fetchall()
            return [
                {
                    'category': row['category'],
                    'name': row['name'],
                    'value': row['value'],
                    'timestamp': row['timestamp']
                }
                for row in rows
            ]
        except sqlite3.Error as e:
            logger.error(f"Error getting metric history: {str(e)}")
            return []

# Add more utility functions as needed