"""
Todo command handlers for PatchPilot.
This module contains the implementation of todo-related commands.
"""

from typing import Optional
from core.models import TodoItem
from core.db_utils import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class TodoCommands:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def complete_todo(self, todo_id: int) -> bool:
        """Mark a todo item as completed."""
        try:
            cursor = self.db_manager.conn.cursor()
            cursor.execute(
                "UPDATE todos SET completed = 1 WHERE id = ?",
                (todo_id,)
            )
            self.db_manager.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error completing todo: {str(e)}")
            return False

    def uncomplete_todo(self, todo_id: int) -> bool:
        """Mark a todo item as not completed."""
        try:
            cursor = self.db_manager.conn.cursor()
            cursor.execute(
                "UPDATE todos SET completed = 0 WHERE id = ?",
                (todo_id,)
            )
            self.db_manager.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error uncompleting todo: {str(e)}")
            return False

    def delete_todo(self, todo_id: int) -> bool:
        """Delete a todo item."""
        try:
            cursor = self.db_manager.conn.cursor()
            cursor.execute(
                "DELETE FROM todos WHERE id = ?",
                (todo_id,)
            )
            self.db_manager.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting todo: {str(e)}")
            return False

    def search_todos(self, query: str) -> list[TodoItem]:
        """Search todos by title or description."""
        try:
            cursor = self.db_manager.conn.cursor()
            cursor.execute(
                """
                SELECT id, title, description, completed, created_at 
                FROM todos 
                WHERE title LIKE ? OR description LIKE ?
                GROUP BY title
                """,
                (f"%{query}%", f"%{query}%")
            )
            rows = cursor.fetchall()
            return [
                TodoItem(
                    id=row[0],
                    title=row[1],
                    description=row[2],
                    completed=bool(row[3]),
                    created_at=row[4]
                )
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Error searching todos: {str(e)}")
            return []

    def clear_todos(self, completed_only: bool = False) -> int:
        """Clear todos from the database.
        
        Args:
            completed_only: If True, only clear completed todos. If False, clear all todos.
            
        Returns:
            Number of todos that were cleared.
        """
        try:
            cursor = self.db_manager.conn.cursor()
            if completed_only:
                cursor.execute("DELETE FROM todos WHERE completed = 1")
            else:
                cursor.execute("DELETE FROM todos")
            
            deleted_count = cursor.rowcount
            self.db_manager.conn.commit()
            return deleted_count
        except Exception as e:
            logger.error(f"Error clearing todos: {str(e)}")
            return 0 