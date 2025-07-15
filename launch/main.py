# main.py
# This file is the entry point of the application

import os
import logging
import argparse
from db_utils import DatabaseManager
from models import TodoItem
from todo_commands import TodoCommands
from typing import Optional, List
import groq
from html_generator import HtmlGenerator
from code_generator import CodeGenerator, CodeTask
import sys
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoDatabaseManager:
    def __init__(self, db_path: str):
        self.db_manager = DatabaseManager(db_path)
        self.todo_commands = TodoCommands(self.db_manager)
        self.html_generator = HtmlGenerator()
        # Get Groq API key
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable not found")
        # Initialize Groq client
        self.client = groq.Groq(api_key=self.groq_api_key)
        # Initialize code generator
        self.code_generator = CodeGenerator(api_key=self.groq_api_key)

    def analyze_database_issue(self, error_message: str) -> dict:
        """Use OpenAI to analyze database issues and suggest fixes."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a database expert. Analyze the following error and suggest fixes."},
                    {"role": "user", "content": f"Database error: {error_message}"}
                ]
            )
            return {
                "analysis": response.choices[0].message.content,
                "suggested_fix": self._extract_fix_suggestion(response.choices[0].message.content)
            }
        except Exception as e:
            logger.error(f"Error in AI analysis: {str(e)}")
            return {"error": str(e)}

    def _extract_fix_suggestion(self, analysis: str) -> str:
        """Extract actionable fix suggestion from AI analysis."""
        # Simple extraction - in practice, you'd want more sophisticated parsing
        return analysis.split("suggested fix:")[-1].strip() if "suggested fix:" in analysis.lower() else analysis

    def autonomous_fix(self, error_message: str) -> bool:
        """Attempt to autonomously fix database issues."""
        try:
            analysis = self.analyze_database_issue(error_message)
            if "error" in analysis:
                return False
            
            logger.info(f"AI Analysis: {analysis['analysis']}")
            logger.info(f"Attempting fix: {analysis['suggested_fix']}")
            
            # Implement fix based on AI suggestion
            # This is a simplified version - in practice, you'd want more sophisticated fix implementation
            if "permission" in error_message.lower():
                self.db_manager.fix_permissions()
            elif "corrupt" in error_message.lower():
                self.db_manager.repair_corruption()
            
            return True
        except Exception as e:
            logger.error(f"Error in autonomous fix: {str(e)}")
            return False

    def add_todo(self, title: str, description: str = None) -> bool:
        """Add a new todo item."""
        todo = TodoItem(title=title, description=description)
        return self.db_manager.add_todo(todo)

    def list_todos(self) -> None:
        """List all todo items."""
        todos = self.db_manager.get_todos()
        if not todos:
            logger.info("No todos found.")
            return
        
        logger.info("Current todos:")
        for todo in todos:
            status = "✓" if todo.completed else " "
            logger.info(f"[{status}] {todo.id}: {todo.title}")
            if todo.description:
                logger.info(f"    {todo.description}")

    def complete_todo(self, todo_id: int) -> None:
        """Mark a todo as completed."""
        if self.todo_commands.complete_todo(todo_id):
            logger.info(f"Todo {todo_id} marked as completed!")
        else:
            logger.error(f"Failed to complete todo {todo_id}")

    def uncomplete_todo(self, todo_id: int) -> None:
        """Mark a todo as not completed."""
        if self.todo_commands.uncomplete_todo(todo_id):
            logger.info(f"Todo {todo_id} marked as not completed!")
        else:
            logger.error(f"Failed to uncomplete todo {todo_id}")

    def delete_todo(self, todo_id: int) -> None:
        """Delete a todo."""
        if self.todo_commands.delete_todo(todo_id):
            logger.info(f"Todo {todo_id} deleted!")
        else:
            logger.error(f"Failed to delete todo {todo_id}")

    def search_todos(self, query: str) -> None:
        """Search todos."""
        todos = self.todo_commands.search_todos(query)
        if not todos:
            logger.info(f"No todos found matching '{query}'")
            return
        
        logger.info(f"Todos matching '{query}':")
        for todo in todos:
            status = "✓" if todo.completed else " "
            logger.info(f"[{status}] {todo.id}: {todo.title}")
            if todo.description:
                logger.info(f"    {todo.description}")

    def generate_blog(self, title: str) -> bool:
        """Generate a blog site with the given title."""
        try:
            return self.html_generator.generate_blog_site(title)
        except Exception as e:
            logger.error(f"Error generating blog: {str(e)}")
            return False

    def generate_code(self, description: str, language: str, requirements: List[str], context: Optional[str] = None) -> bool:
        """Generate code based on description and requirements."""
        try:
            task = CodeTask(
                description=description,
                language=language,
                requirements=requirements,
                context=context
            )
            
            # Generate the code
            generated_code = self.code_generator.generate_code(task)
            logger.info(f"Generated code for: {description}")
            
            # Save the code and tests
            if self.code_generator.save_code(generated_code):
                logger.info(f"Saved code to: {generated_code.file_path}")
                
                # Run tests if available
                if generated_code.tests:
                    success, output = self.code_generator.run_tests(generated_code)
                    if success:
                        logger.info("All tests passed!")
                    else:
                        logger.warning(f"Tests failed:\n{output}")
                        
                        # Try to improve the code based on test failures
                        improved_code = self.code_generator.improve_code(
                            generated_code,
                            f"Fix the following test failures:\n{output}"
                        )
                        
                        # Save and test the improved code
                        if self.code_generator.save_code(improved_code):
                            success, output = self.code_generator.run_tests(improved_code)
                            if success:
                                logger.info("Code improved and all tests now pass!")
                            else:
                                logger.warning("Code still needs improvement")
                
                return True
            else:
                logger.error("Failed to save generated code")
                return False
                
        except Exception as e:
            logger.error(f"Error in code generation: {str(e)}")
            return False

    def run_patch(self, patch_id: str) -> bool:
        """Run a generated patch.
        
        Args:
            patch_id: The patch ID (directory name) to run
            
        Returns:
            bool: True if patch ran successfully, False otherwise
        """
        try:
            # Construct patch directory path
            patch_dir = os.path.join(self.code_generator.patches_dir, patch_id)
            if not os.path.exists(patch_dir):
                logger.error(f"Patch directory not found: {patch_dir}")
                return False
                
            # Read metadata to determine language and requirements
            metadata_path = os.path.join(patch_dir, "metadata.txt")
            if not os.path.exists(metadata_path):
                logger.error(f"Metadata file not found: {metadata_path}")
                return False
                
            # Parse metadata
            task = None
            with open(metadata_path, 'r') as f:
                metadata_lines = f.readlines()
                description = None
                language = None
                requirements = []
                context = None
                
                for line in metadata_lines:
                    if line.startswith("Task Description: "):
                        description = line.split("Task Description: ")[1].strip()
                    elif line.startswith("Language: "):
                        language = line.split("Language: ")[1].strip().lower()
                    elif line.startswith("Requirements:"):
                        # Read requirements until empty line or different section
                        i = metadata_lines.index(line) + 1
                        while i < len(metadata_lines) and metadata_lines[i].strip() and metadata_lines[i].startswith("- "):
                            requirements.append(metadata_lines[i].strip("- \n"))
                            i += 1
                    elif line.startswith("Context:"):
                        # Read context until empty line or different section
                        i = metadata_lines.index(line) + 1
                        context_lines = []
                        while i < len(metadata_lines) and metadata_lines[i].strip() and not metadata_lines[i].startswith("- "):
                            context_lines.append(metadata_lines[i].strip())
                            i += 1
                        context = "\n".join(context_lines)
                
            if not language:
                logger.error("Language not found in metadata")
                return False
                
            # Create CodeTask object for improvement
            task = CodeTask(
                description=description or "Unknown task",
                language=language,
                requirements=requirements,
                context=context
            )
                
            # Install requirements if Python
            if language == "python":
                requirements_path = os.path.join(patch_dir, "requirements.txt")
                if os.path.exists(requirements_path):
                    try:
                        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
                    except subprocess.CalledProcessError as e:
                        logger.error(f"Failed to install requirements: {str(e)}")
                        return False
                        
            # Run and improve the code
            success, output = self.code_generator.run_and_improve(patch_dir, task)
            
            if success:
                logger.info("Patch execution successful!")
                logger.info("Output:")
                logger.info(output)
                return True
            else:
                logger.error(f"Patch execution failed: {output}")
                return False
                
        except Exception as e:
            logger.error(f"Error running patch: {str(e)}")
            return False

def main():
    parser = argparse.ArgumentParser(description='AutoCodeRover - AI-powered development tool')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Add todo command
    add_parser = subparsers.add_parser('add', help='Add a new todo item')
    add_parser.add_argument('title', help='Title of the todo item')
    add_parser.add_argument('--description', '-d', help='Description of the todo item')

    # List todos command
    subparsers.add_parser('list', help='List all todo items')

    # Complete todo command
    complete_parser = subparsers.add_parser('complete', help='Mark a todo as completed')
    complete_parser.add_argument('id', type=int, help='ID of the todo item')

    # Uncomplete todo command
    uncomplete_parser = subparsers.add_parser('uncomplete', help='Mark a todo as not completed')
    uncomplete_parser.add_argument('id', type=int, help='ID of the todo item')

    # Delete todo command
    delete_parser = subparsers.add_parser('delete', help='Delete a todo item')
    delete_parser.add_argument('id', type=int, help='ID of the todo item')

    # Search todos command
    search_parser = subparsers.add_parser('search', help='Search todo items')
    search_parser.add_argument('query', help='Search query')

    # Fix database command
    fix_parser = subparsers.add_parser('fix', help='Fix database issues')
    fix_parser.add_argument('error', help='Error message or issue description')

    # Analyze database command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze database issues without fixing')
    analyze_parser.add_argument('error', help='Error message or issue description')

    # Generate blog command
    blog_parser = subparsers.add_parser('generate-blog', help='Generate a blog site')
    blog_parser.add_argument('title', help='Title of the blog')

    # Generate code command
    code_parser = subparsers.add_parser('generate-code', help='Generate code autonomously')
    code_parser.add_argument('description', help='Description of what the code should do')
    code_parser.add_argument('--language', '-l', default='python', help='Programming language (default: python)')
    code_parser.add_argument('--requirements', '-r', nargs='+', help='List of requirements')
    code_parser.add_argument('--context', '-c', help='Additional context for code generation')

    # Run patch command
    run_parser = subparsers.add_parser('run-patch', help='Run a generated patch')
    run_parser.add_argument('patch_id', help='ID (directory name) of the patch to run')

    args = parser.parse_args()
    
    # Use DB_PATH from environment or default to todos.db
    db_path = os.getenv('DB_PATH', 'todos.db')
    auto_manager = AutoDatabaseManager(db_path)
    
    try:
        if args.command == 'add':
            if auto_manager.add_todo(args.title, args.description):
                logger.info("Todo added successfully!")
            else:
                logger.error("Failed to add todo.")
        
        elif args.command == 'list':
            auto_manager.list_todos()
        
        elif args.command == 'complete':
            auto_manager.complete_todo(args.id)
        
        elif args.command == 'uncomplete':
            auto_manager.uncomplete_todo(args.id)
        
        elif args.command == 'delete':
            auto_manager.delete_todo(args.id)
        
        elif args.command == 'search':
            auto_manager.search_todos(args.query)
        
        elif args.command == 'fix':
            result = auto_manager.autonomous_fix(args.error)
            if result:
                logger.info("Database issue fixed successfully!")
            else:
                logger.error("Could not fix database issue automatically.")
        
        elif args.command == 'analyze':
            analysis = auto_manager.analyze_database_issue(args.error)
            if "error" not in analysis:
                logger.info("\nAnalysis:")
                logger.info(analysis["analysis"])
                logger.info("\nSuggested fix:")
                logger.info(analysis["suggested_fix"])
            else:
                logger.error("Could not analyze database issue.")
        
        elif args.command == 'generate-blog':
            if auto_manager.generate_blog(args.title):
                logger.info("Blog site generated successfully!")
            else:
                logger.error("Failed to generate blog site.")
        
        elif args.command == 'generate-code':
            requirements = args.requirements if args.requirements else ["Write clean, efficient code"]
            if auto_manager.generate_code(args.description, args.language, requirements, args.context):
                logger.info("Code generated successfully!")
            else:
                logger.error("Failed to generate code.")

        elif args.command == 'run-patch':
            if auto_manager.run_patch(args.patch_id):
                logger.info(f"Patch {args.patch_id} ran successfully!")
            else:
                logger.error(f"Failed to run patch {args.patch_id}")
        
        else:
            parser.print_help()

    except Exception as e:
        logger.error(f"Error: {str(e)}")
    finally:
        auto_manager.db_manager.close()

if __name__ == "__main__":
    main()