import os
import unittest
from datetime import datetime
from code_generator import CodeGenerator, CodeTask
import shutil

class TestCodeGenerator(unittest.TestCase):
    def setUp(self):
        self.test_project_dir = "test_project"
        self.api_key = os.getenv("GROQ_API_KEY", "dummy_key")
        self.code_generator = CodeGenerator(self.api_key, self.test_project_dir)
        
        # Create test project directory if it doesn't exist
        if not os.path.exists(self.test_project_dir):
            os.makedirs(self.test_project_dir)

    def tearDown(self):
        # Clean up test directories after tests
        if os.path.exists(self.test_project_dir):
            shutil.rmtree(self.test_project_dir)

    def test_patches_directory_creation(self):
        """Test that patches directory is created correctly."""
        patches_dir = os.path.join(self.test_project_dir, "patches")
        self.assertTrue(os.path.exists(patches_dir), "Patches directory should be created")

    def test_patch_directory_structure(self):
        """Test the structure of generated patch directory."""
        # Create a test task
        task = CodeTask(
            description="Create a simple hello world function",
            language="python",
            requirements=["Function should return 'Hello, World!'"],
            context="Unit test context"
        )

        # Generate code
        generated_code = self.code_generator.generate_code(task)

        # Get the patch directory (it should be the only directory in patches)
        patches_dir = os.path.join(self.test_project_dir, "patches")
        patch_dirs = [d for d in os.listdir(patches_dir) if os.path.isdir(os.path.join(patches_dir, d))]
        self.assertEqual(len(patch_dirs), 1, "Should create exactly one patch directory")
        
        patch_dir = os.path.join(patches_dir, patch_dirs[0])
        
        # Check directory name format
        dir_name = os.path.basename(patch_dir)
        self.assertRegex(dir_name, r"\d{8}_\d{6}_create_a_simple_hello_world_function",
                        "Directory name should match expected format")

        # Check required files exist
        self.assertTrue(os.path.exists(os.path.join(patch_dir, "metadata.txt")),
                       "metadata.txt should exist")
        self.assertTrue(os.path.exists(os.path.join(patch_dir, "README.md")),
                       "README.md should exist")
        
        # Check metadata content
        with open(os.path.join(patch_dir, "metadata.txt"), 'r') as f:
            metadata_content = f.read()
            self.assertIn("Task Description: Create a simple hello world function", metadata_content)
            self.assertIn("Language: python", metadata_content)
            self.assertIn("Requirements:", metadata_content)
            self.assertIn("- Function should return 'Hello, World!'", metadata_content)

        # Check README content
        with open(os.path.join(patch_dir, "README.md"), 'r') as f:
            readme_content = f.read()
            self.assertIn("# Create a simple hello world function", readme_content)
            self.assertIn("Generated at:", readme_content)
            self.assertIn("## Files", readme_content)

    def test_run_patch(self):
        """Test running a generated patch."""
        # Create a test task
        task = CodeTask(
            description="Create a simple hello world function",
            language="python",
            requirements=["Print 'Hello, World!'"],
            context="Unit test context"
        )

        # Generate code
        generated_code = self.code_generator.generate_code(task)

        # Get the patch directory
        patches_dir = os.path.join(self.test_project_dir, "patches")
        patch_dirs = [d for d in os.listdir(patches_dir) if os.path.isdir(os.path.join(patches_dir, d))]
        self.assertEqual(len(patch_dirs), 1, "Should create exactly one patch directory")
        
        patch_dir = os.path.join(patches_dir, patch_dirs[0])
        patch_id = os.path.basename(patch_dir)

        # Create an AutoDatabaseManager instance
        from main import AutoDatabaseManager
        auto_manager = AutoDatabaseManager(":memory:")

        # Run the patch
        result = auto_manager.run_patch(patch_id)
        self.assertTrue(result, "Patch should run successfully")

if __name__ == '__main__':
    unittest.main() 