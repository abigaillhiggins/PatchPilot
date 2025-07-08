import unittest
from src.core.models import TodoItem
from src.core.db_utils import DatabaseManager
from src.generators.code_generator import CodeGenerator, CodeTask
import os
import json
from datetime import datetime
import tempfile
import shutil
from typing import List

class TestWorkflowTaskHandling(unittest.TestCase):
    """Test suite for handling workflow-style tasks."""
    
    def setUp(self):
        """Set up test environment."""
        self.api_key = os.getenv("OPENAI_API_KEY", "sk-mock-key-for-testing")
        self.test_project_dir = tempfile.mkdtemp(prefix="test_workflow_")
        self.db_manager = DatabaseManager(":memory:")
        self.code_generator = CodeGenerator(self.api_key, self.test_project_dir)

    def test_workflow_task_creation(self):
        """Test creating a workflow task through the todo system."""
        # Create a workflow task
        workflow_task = TodoItem(
            title="Travel Dates Planning",
            description="Determine optimal travel dates for China trip considering weather, costs, and visa processing",
            language="python",
            requirements=[
                "Function to fetch weather data for given dates and locations",
                "Function to estimate visa processing time",
                "Function to analyze cost variations by date",
                "Function to validate date ranges against constraints"
            ],
            context="Part of Two-Week China Trip Planning workflow",
            metadata={
                "workflow_name": "Two-Week China Trip Planning",
                "agent_type": "Planner / Travel Consultant",
                "inputs": ["User preferences", "visa requirements", "climate info"],
                "outputs": ["Finalized travel dates"],
                "success_criteria": "Selected travel dates within suitable window",
                "tools_required": False,
                "required_tool_types": []
            }
        )
        
        # Add task to database
        success = self.db_manager.add_todo(workflow_task)
        self.assertTrue(success, "Failed to add workflow task to database")
        
        # Verify task was stored correctly
        todos = self.db_manager.get_todos()
        self.assertEqual(len(todos), 1, "Should have exactly one todo item")
        
        stored_task = todos[0]
        self.assertEqual(stored_task.title, "Travel Dates Planning")
        self.assertEqual(stored_task.metadata["workflow_name"], "Two-Week China Trip Planning")
        self.assertEqual(len(stored_task.requirements), 4)

        # Generate actual code for the workflow
        code_task = CodeTask(
            description=stored_task.description,
            language=stored_task.language,
            requirements=stored_task.requirements,
            context=json.dumps(stored_task.metadata)
        )
        
        generated_code = self.code_generator.generate_code(code_task)
        self.assertIsNotNone(generated_code, "Should generate code")
        self.assertIsNotNone(generated_code.content, "Generated code should have content")
        
        # Verify the generated code has all required functions
        self.assertIn("def fetch_weather_data", generated_code.content)
        self.assertIn("def estimate_visa_processing_time", generated_code.content)
        self.assertIn("def analyze_cost_variation_by_date", generated_code.content)
        self.assertIn("def validate_date_range", generated_code.content)
        
        # Verify the code has proper type hints and docstrings
        self.assertIn("start_date: datetime.date", generated_code.content)
        self.assertIn("end_date: datetime.date", generated_code.content)
        self.assertIn("locations: List[str]", generated_code.content)
        self.assertIn("country: str", generated_code.content)
        self.assertIn("\"\"\"", generated_code.content)  # Should have docstrings
        
        # Run the generated code to verify it works
        exec(generated_code.content)

        # Clean up
        shutil.rmtree(self.test_project_dir)

if __name__ == '__main__':
    unittest.main() 