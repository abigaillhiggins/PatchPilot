#!/usr/bin/env python3

import requests
import json
import time
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CodeGenPipeline:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()

    def create_todo(self, title: str, description: str, language: str = "python", 
                   requirements: Optional[List[str]] = None, context: Optional[str] = None,
                   metadata: Optional[Dict] = None) -> Dict:
        """Create a new todo item with code generation metadata."""
        payload = {
            "title": title,
            "description": description,
            "language": language,
            "requirements": requirements or [],
            "context": context,
            "metadata": metadata or {}
        }

        response = self.session.post(
            f"{self.base_url}/todos/",
            json=payload
        )
        response.raise_for_status()
        logger.info(f"Created TODO: {title}")
        return response.json()

    def list_todos(self) -> List[Dict]:
        """List all todos."""
        response = self.session.get(f"{self.base_url}/todos/")
        response.raise_for_status()
        return response.json()

    def generate_code(self, todo_id: int) -> Dict:
        """Generate code for a specific todo item."""
        response = self.session.post(f"{self.base_url}/generate-code/{todo_id}")
        response.raise_for_status()
        result = response.json()
        logger.info(f"Code generation initiated for todo {todo_id}")
        return result

    def run_patch(self, todo_id: int) -> Dict:
        """Run the generated patch for a specific todo."""
        response = self.session.post(f"{self.base_url}/run-patch/{todo_id}")
        response.raise_for_status()
        logger.info(f"Patch execution initiated for todo {todo_id}")
        return response.json()

    def get_patch_status(self, patch_id: str) -> Dict:
        """Get the status of a patch."""
        if not patch_id:
            raise ValueError("Patch ID cannot be None")
        response = self.session.get(f"{self.base_url}/patch-status/{patch_id}")
        response.raise_for_status()
        return response.json()

    def git_init(self) -> Dict:
        """Initialize git repository."""
        response = self.session.post(f"{self.base_url}/git/init")
        response.raise_for_status()
        logger.info("Git repository initialized")
        return response.json()

    def git_config(self, name: str, email: str) -> Dict:
        """Configure git user."""
        response = self.session.post(
            f"{self.base_url}/git/config",
            json={"name": name, "email": email}
        )
        response.raise_for_status()
        logger.info(f"Git configured for user: {name}")
        return response.json()

    def git_add_remote(self, name: str, url: str) -> Dict:
        """Add git remote."""
        response = self.session.post(
            f"{self.base_url}/git/remote",
            json={"name": name, "url": url}
        )
        response.raise_for_status()
        logger.info(f"Added remote {name}: {url}")
        return response.json()

    def git_commit(self, message: str, files: List[str]) -> Dict:
        """Commit changes."""
        response = self.session.post(
            f"{self.base_url}/git/commit",
            json={"message": message, "files": files}
        )
        response.raise_for_status()
        logger.info(f"Committed changes: {message}")
        return response.json()

    def git_push(self, branch: str = "main") -> Dict:
        """Push changes to remote."""
        response = self.session.post(
            f"{self.base_url}/git/push",
            json={"branch": branch}
        )
        response.raise_for_status()
        logger.info(f"Pushed changes to {branch}")
        return response.json()

    def create_improvement_todo(self, original_todo_id: int) -> Optional[Dict]:
        """Create a new todo item based on improvements needed for a previous todo.
        
        Args:
            original_todo_id: ID of the original todo to analyze for improvements
            
        Returns:
            Optional[Dict]: The newly created todo item if successful, None otherwise
        """
        try:
            # Get the original todo
            original_todo = self.session.get(f"{self.base_url}/todos/{original_todo_id}").json()
            if not original_todo.get('patch_id'):
                logger.error(f"No patch found for todo {original_todo_id}")
                return None
                
            # Get patch status and analysis
            patch_status = self.get_patch_status(original_todo['patch_id'])
            if not patch_status.get('analysis'):
                logger.error(f"No analysis available for patch {original_todo['patch_id']}")
                return None
                
            # Create improvement todo
            improvement_todo = {
                "title": f"Improve: {original_todo['title']}",
                "description": f"Implement improvements based on analysis of previous implementation:\n\n{patch_status['analysis']}",
                "language": original_todo.get('language', 'python'),
                "requirements": original_todo.get('requirements', []),
                "context": f"This is an improvement task based on todo #{original_todo_id}. Previous patch ID: {original_todo['patch_id']}",
                "metadata": {
                    "original_todo_id": original_todo_id,
                    "original_patch_id": original_todo['patch_id'],
                    "improvements_needed": patch_status.get('fixes', [])
                }
            }
            
            # Create the new todo
            response = self.create_todo(
                title=improvement_todo["title"],
                description=improvement_todo["description"],
                language=improvement_todo["language"],
                requirements=improvement_todo["requirements"],
                context=improvement_todo["context"],
                metadata=improvement_todo["metadata"]
            )
            
            logger.info(f"Created improvement todo based on todo {original_todo_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error creating improvement todo: {str(e)}")
            return None

def demonstrate_pipeline():
    """Demonstrate the complete code generation pipeline."""
    pipeline = CodeGenPipeline()
    
    # Initialize git
    pipeline.git_init()
    pipeline.git_config("Your Name", "your.email@example.com")
    pipeline.git_add_remote("origin", "https://github.com/yourusername/yourrepo.git")

    # Create a series of related todos with code generation metadata
    todos = [
        {
            "title": "Create Data Validator Class",
            "description": "Generate a Python class that validates JSON data against a schema",
            "language": "python",
            "requirements": ["jsonschema", "pytest"],
            "context": "We need a reusable validator class that can validate JSON data against predefined schemas",
            "metadata": {
                "test_requirements": ["pytest"],
                "coverage_target": "90%"
            }
        },
        {
            "title": "Add Validation Tests",
            "description": "Generate comprehensive unit tests for the validator",
            "language": "python",
            "requirements": ["pytest", "pytest-cov"],
            "context": "Create tests for the JSON validator class, including edge cases",
            "metadata": {
                "test_framework": "pytest",
                "coverage_target": "90%"
            }
        }
    ]

    # Process each todo
    for todo in todos:
        try:
            # Create todo with code generation metadata
            created_todo = pipeline.create_todo(
                todo["title"],
                todo["description"],
                todo["language"],
                todo.get("requirements"),
                todo.get("context"),
                todo.get("metadata")
            )
            logger.info(f"Created todo: {created_todo}")

            # Generate code using todo ID
            gen_result = pipeline.generate_code(created_todo["id"])
            patch_id = gen_result.get("patch_id")
            
            # Run patch
            run_result = pipeline.run_patch(created_todo["id"])
            
            # Wait for patch completion
            while True:
                status = pipeline.get_patch_status(patch_id)
                if status.get("status") == "completed":
                    break
                time.sleep(2)
            
            # Commit and push changes
            pipeline.git_commit(
                f"Add {todo['title']}",
                [f"patches/{patch_id}/*"]
            )
            pipeline.git_push()
            
            logger.info(f"Successfully processed todo: {todo['title']}")
            
        except Exception as e:
            logger.error(f"Error processing todo {todo['title']}: {str(e)}")

if __name__ == "__main__":
    try:
        demonstrate_pipeline()
    except Exception as e:
        logger.error(f"Pipeline demonstration failed: {str(e)}") 