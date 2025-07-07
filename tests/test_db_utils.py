# test_db_utils.py
# Placeholder content for test_db_utils.py
# This file would contain unit tests for the db_utils.py functions

import os
import unittest
from db_utils import DatabaseManager
from models import TodoItem
from todo_commands import TodoCommands

class TestDatabaseManager(unittest.TestCase):
    """Test cases for DatabaseManager class."""

    def setUp(self):
        """Set up test environment."""
        self.test_db = "test_todos.db"
        self.db_manager = DatabaseManager(self.test_db)
        self.todo_commands = TodoCommands(self.db_manager)

    def tearDown(self):
        """Clean up test environment."""
        self.db_manager.close()
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_add_todo(self):
        """Test adding a todo item."""
        todo = TodoItem(title="Test todo", description="Test description")
        self.assertTrue(self.db_manager.add_todo(todo))
        
        todos = self.db_manager.get_todos()
        self.assertEqual(len(todos), 1)
        self.assertEqual(todos[0].title, "Test todo")
        self.assertEqual(todos[0].description, "Test description")
        self.assertFalse(todos[0].completed)

    def test_complete_todo(self):
        """Test completing a todo item."""
        # Add a todo
        todo = TodoItem(title="Test todo")
        self.db_manager.add_todo(todo)
        todos = self.db_manager.get_todos()
        todo_id = todos[0].id

        # Complete it
        self.assertTrue(self.todo_commands.complete_todo(todo_id))
        
        # Verify it's completed
        todos = self.db_manager.get_todos()
        self.assertEqual(len(todos), 1)
        self.assertTrue(todos[0].completed)

    def test_uncomplete_todo(self):
        """Test uncompleting a todo item."""
        # Add a completed todo
        todo = TodoItem(title="Test todo", completed=True)
        self.db_manager.add_todo(todo)
        todos = self.db_manager.get_todos()
        todo_id = todos[0].id

        # Uncomplete it
        self.assertTrue(self.todo_commands.uncomplete_todo(todo_id))
        
        # Verify it's not completed
        todos = self.db_manager.get_todos()
        self.assertEqual(len(todos), 1)
        self.assertFalse(todos[0].completed)

    def test_delete_todo(self):
        """Test deleting a todo item."""
        # Add a todo
        todo = TodoItem(title="Test todo")
        self.db_manager.add_todo(todo)
        todos = self.db_manager.get_todos()
        todo_id = todos[0].id

        # Delete it
        self.assertTrue(self.todo_commands.delete_todo(todo_id))
        
        # Verify it's deleted
        todos = self.db_manager.get_todos()
        self.assertEqual(len(todos), 0)

    def test_search_todos(self):
        """Test searching todo items."""
        # Add some todos
        todos = [
            TodoItem(title="Buy groceries", description="Get milk and bread"),
            TodoItem(title="Do laundry"),
            TodoItem(title="Buy milk", description="2% milk"),
        ]
        for todo in todos:
            self.db_manager.add_todo(todo)

        # Search for 'milk'
        results = self.todo_commands.search_todos("milk")
        self.assertEqual(len(results), 2)
        titles = {todo.title for todo in results}
        self.assertIn("Buy groceries", titles)
        self.assertIn("Buy milk", titles)

        # Search for 'laundry'
        results = self.todo_commands.search_todos("laundry")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Do laundry")

        # Search for non-existent term
        results = self.todo_commands.search_todos("nonexistent")
        self.assertEqual(len(results), 0)

if __name__ == '__main__':
    unittest.main()