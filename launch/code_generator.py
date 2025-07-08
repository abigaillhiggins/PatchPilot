"""
Autonomous code generation module for AutoCodeRover.
This module provides functionality to generate, test, and manage code autonomously.
"""

import os
import logging
import subprocess
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from openai import OpenAI
import ast
import black
import autopep8
import shutil
import sys
import json

logger = logging.getLogger(__name__)

@dataclass
class CodeTask:
    """Represents a coding task with requirements and context."""
    description: str
    language: str
    requirements: List[str]
    context: Optional[str] = None
    created_at: str = datetime.now().isoformat()
    config_files: Optional[List[str]] = None

@dataclass
class GeneratedCode:
    """Represents generated code with metadata."""
    content: str
    language: str
    file_path: str
    description: str
    tests: Optional[str] = None
    created_at: str = datetime.now().isoformat()

def clean_code_document(code: str) -> str:
    """Clean code document by removing markdown formatting and triple quotes.
    
    Args:
        code: Raw code string that may contain markdown formatting
        
    Returns:
        Clean code string with markdown formatting removed
    """
    # Remove leading/trailing whitespace
    code = code.strip()
    
    # Remove triple quotes if present
    if code.startswith("'''") and code.endswith("'''"):
        code = code[3:-3].strip()
    elif code.startswith('"""') and code.endswith('"""'):
        code = code[3:-3].strip()
    
    # Remove ```python at start if present
    if code.startswith("```python"):
        code = code[len("```python"):].lstrip()
    elif code.startswith("```"):
        code = code[3:].lstrip()
        
    if code.endswith("```"):
        code = code[:-3].rstrip()
        
    # Remove any remaining ``` markers
    code = code.replace("```python", "").replace("```", "").strip()
    
    return code

def clean_file_of_triple_quotes(file_path: str) -> None:
    """Remove surrounding Python multi-line string quotes from a file's content.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        None
    """
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Remove triple quotes if present
        if content.startswith("'''") and content.endswith("'''"):
            content = content[3:-3].strip()
        elif content.startswith('"""') and content.endswith('"""'):
            content = content[3:-3].strip()
            
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    except Exception as e:
        logger.error(f"Failed to clean triple quotes from file {file_path}: {str(e)}")

def clean_file_of_backticks(file_path: str) -> None:
    """Remove triple backticks and language tags from a file's content.
    
    Args:
        file_path: Path to the file to clean.
    """
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Remove triple backticks and language tags
        if content.startswith("```python"):
            content = content[len("```python"):].lstrip()
        elif content.startswith("```"):
            content = content[3:].lstrip()
            
        if content.endswith("```"):
            content = content[:-3].rstrip()
            
        # Remove any remaining backticks
        content = content.replace("```python", "").replace("```", "").strip()
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    except Exception as e:
        logger.error(f"Failed to clean file {file_path}: {str(e)}")

class CodeGenerator:
    """Manages autonomous code generation and testing."""
    
    LANGUAGE_EXTENSIONS = {
        # Programming Languages
        'python': '.py',
        'javascript': '.js',
        'typescript': '.ts',
        'java': '.java',
        'cpp': '.cpp',
        'c': '.c',
        'csharp': '.cs',
        'go': '.go',
        'rust': '.rs',
        'ruby': '.rb',
        'php': '.php',
        'swift': '.swift',
        'kotlin': '.kt',
        
        # Web Technologies
        'html': '.html',
        'css': '.css',
        'scss': '.scss',
        'less': '.less',
        'jsx': '.jsx',
        'tsx': '.tsx',
        'vue': '.vue',
        
        # Data/Config Formats
        'json': '.json',
        'yaml': '.yml',
        'toml': '.toml',
        'ini': '.ini',
        'xml': '.xml',
        
        # Shell/Scripts
        'shell': '.sh',
        'bash': '.sh',
        'powershell': '.ps1',
        'batch': '.bat',
        
        # Documentation
        'markdown': '.md',
        'text': '.txt',
        'restructuredtext': '.rst'
    }

    LANGUAGE_TEST_PREFIXES = {
        'python': 'test_',
        'javascript': 'test.',
        'typescript': 'test.',
        'java': 'Test',
        'cpp': 'test_',
        'csharp': 'Test',
        'go': '_test',
        'rust': 'test_',
        'ruby': 'test_',
        'php': 'Test',
        'kotlin': 'Test'
    }

    LANGUAGE_DIRECTORIES = {
        # Python Project Structure
        'python': {
            'src': 'src',
            'tests': 'tests',
            'docs': 'docs',
            'config': 'config',
            'scripts': 'scripts',
            'resources': 'resources'
        },
        
        # JavaScript/TypeScript Project Structure
        'javascript': {
            'src': 'src',
            'tests': 'tests',
            'dist': 'dist',
            'config': 'config',
            'scripts': 'scripts',
            'types': 'types'
        },
        'typescript': {
            'src': 'src',
            'tests': 'tests',
            'dist': 'dist',
            'config': 'config',
            'scripts': 'scripts',
            'types': 'types'
        },
        
        # Web Project Structure
        'html': {
            'css': 'css',
            'js': 'js',
            'assets': 'assets',
            'images': 'assets/images',
            'fonts': 'assets/fonts'
        },
        
        # Java Project Structure
        'java': {
            'src': 'src/main/java',
            'resources': 'src/main/resources',
            'tests': 'src/test/java',
            'test_resources': 'src/test/resources',
            'config': 'config'
        },
        
        # Go Project Structure
        'go': {
            'cmd': 'cmd',
            'internal': 'internal',
            'pkg': 'pkg',
            'api': 'api',
            'tests': 'tests',
            'docs': 'docs'
        },
        
        # Rust Project Structure
        'rust': {
            'src': 'src',
            'tests': 'tests',
            'examples': 'examples',
            'benches': 'benches',
            'docs': 'docs'
        }
    }

    CONFIG_FILES = {
        'python': [
            ('requirements.txt', 'Package dependencies'),
            ('setup.py', 'Package setup configuration'),
            ('pyproject.toml', 'Project configuration'),
            ('.env', 'Environment variables'),
            ('config.json', 'Application configuration')
        ],
        'javascript': [
            ('package.json', 'Package configuration'),
            ('.npmrc', 'NPM configuration'),
            ('tsconfig.json', 'TypeScript configuration'),
            ('.env', 'Environment variables'),
            ('config.json', 'Application configuration')
        ],
        'java': [
            ('pom.xml', 'Maven configuration'),
            ('build.gradle', 'Gradle configuration'),
            ('application.properties', 'Application properties'),
            ('application.yml', 'YAML configuration')
        ],
        'go': [
            ('go.mod', 'Go modules file'),
            ('go.sum', 'Go modules checksum'),
            ('config.json', 'Application configuration')
        ],
        'rust': [
            ('Cargo.toml', 'Cargo configuration'),
            ('Cargo.lock', 'Cargo lock file'),
            ('config.json', 'Application configuration')
        ]
    }

    def __init__(self, api_key: str, project_dir: str = "."):
        """Initialize the code generator."""
        self.project_dir = project_dir
        self.patches_dir = os.path.join(project_dir, "patches")
        self._ensure_directories_exist()
        self.max_improvement_attempts = 3  # Maximum number of recursive improvement attempts

        # Validate API key
        if not (api_key and len(api_key) > 40 and api_key.startswith('sk-')):
            raise ValueError("Invalid OpenAI API key format")

        # Validate and initialize OpenAI client
        if not api_key or api_key == "dummy_key_for_testing":
            self.client = None
            logger.warning("No valid API key provided. Code generation and analysis features will be disabled.")
            return

        # Import validation function
        try:
            from test_api_key import validate_api_key_format
            is_valid, error = validate_api_key_format(api_key)
            if not is_valid:
                self.client = None
                logger.warning(f"Invalid OpenAI API key format: {error}. Code generation will be disabled.")
                return
        except ImportError:
            # Fallback to basic validation if test_api_key module not available
            if not (api_key and len(api_key) > 40 and (api_key.startswith('sk-') or api_key.startswith('sk-proj-'))):
                self.client = None
                logger.warning("Invalid OpenAI API key format. Code generation will be disabled.")
                return

        try:
            self.client = OpenAI(api_key=api_key)
            # Test the client with a minimal API call
            self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "system", "content": "Test"}, {"role": "user", "content": "Test"}],
                max_tokens=1
            )
            logger.info("OpenAI API key validated successfully.")
        except Exception as e:
            self.client = None
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            logger.warning("Code generation and analysis features will be disabled.")

    def _ensure_directories_exist(self):
        """Create necessary directories if they don't exist."""
        os.makedirs(self.project_dir, exist_ok=True)
        os.makedirs(self.patches_dir, exist_ok=True)

    def _get_patch_directory(self, task: CodeTask) -> str:
        """Create a unique patch directory for the task."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_description = "".join(c if c.isalnum() else "_" for c in task.description.lower())
        patch_dir = os.path.join(self.patches_dir, f"{timestamp}_{safe_description[:50]}")
        os.makedirs(patch_dir, exist_ok=True)
        return patch_dir

    def _create_language_directories(self, patch_dir: str, language: str) -> None:
        """Create language-specific directories in the patch directory."""
        # Only create src directory
        src_dir = os.path.join(patch_dir, 'src')
        os.makedirs(src_dir, exist_ok=True)

    def _create_config_files(self, patch_dir: str, task: CodeTask) -> None:
        """Create basic requirements.txt file."""
        # Only create requirements.txt
        if task.language.lower() == 'python':
            with open(os.path.join(patch_dir, 'requirements.txt'), 'w') as f:
                f.write("# Python dependencies\n")
                f.write("pytest>=7.0.0\n")  # Always include pytest for testing
                # Add task-specific requirements
                for req in task.requirements:
                    if '>=' in req or '==' in req or '<=' in req:
                        # If requirement already has version specifier, use as is
                        f.write(f"{req}\n")
                    else:
                        # If no version specifier, add latest version
                        f.write(f"{req}>=1.0.0\n")

    def _format_code(self, code: str, language: str) -> str:
        """Format the generated code according to language standards."""
        try:
            if language.lower() == 'python':
                # Try black first
                try:
                    return black.format_str(code, mode=black.FileMode())
                except:
                    # Fall back to autopep8
                    return autopep8.fix_code(code)
            # Add formatters for other languages here
            return code
        except Exception as e:
            logger.warning(f"Failed to format code: {str(e)}")
            return code

    def _generate_file_name(self, task: CodeTask) -> str:
        """Generate an appropriate file name for the code."""
        safe_name = "".join(c if c.isalnum() else "_" for c in task.description.lower())
        extension = self.LANGUAGE_EXTENSIONS.get(task.language.lower(), '.txt')
        return f"{safe_name[:50]}{extension}"

    def _get_test_prefix(self, language: str) -> str:
        """Get the appropriate test file prefix for the language."""
        return self.LANGUAGE_TEST_PREFIXES.get(language.lower(), 'test_')

    def _get_test_file_path(self, source_file: str) -> str:
        """Get the path for the test file corresponding to a source file."""
        dir_name = os.path.dirname(source_file)
        base_name = os.path.basename(source_file)
        test_prefix = self._get_test_prefix(os.path.splitext(base_name)[1][1:])
        return os.path.join(dir_name, f"{test_prefix}{base_name}")

    def _create_generation_prompt(self, task: CodeTask) -> str:
        """Create a detailed prompt for code generation."""
        prompt = f"Generate {task.language} code for: {task.description}\n\n"
        
        # Add requirements
        prompt += "Requirements:\n"
        for req in task.requirements:
            prompt += f"- {req}\n"
        
        # Add task context
        if task.context:
            prompt += f"\nContext:\n{task.context}\n"
        
        return prompt

    def _get_file_path(self, patch_dir: str, file_name: str, task: CodeTask) -> str:
        """Get the appropriate file path based on language and file type."""
        language = task.language.lower()
        
        # Handle configuration files
        if any(file_name == config[0] for config in self.CONFIG_FILES.get(language, [])):
            if file_name in ['requirements.txt', 'setup.py', 'package.json', 'go.mod', 'Cargo.toml']:
                return os.path.join(patch_dir, file_name)
            return os.path.join(patch_dir, 'config', file_name)
        
        # Handle language-specific directories
        if language in self.LANGUAGE_DIRECTORIES:
            dirs = self.LANGUAGE_DIRECTORIES[language]
            
            # Handle test files
            if 'test' in file_name.lower():
                return os.path.join(patch_dir, dirs.get('tests', 'tests'), file_name)
            
            # Handle source files
            if language in ['python', 'javascript', 'typescript', 'java', 'go', 'rust']:
                return os.path.join(patch_dir, dirs.get('src', 'src'), file_name)
            
            # Handle web files
            if language == 'html':
                if file_name.endswith('.css'):
                    return os.path.join(patch_dir, dirs['css'], file_name)
                elif file_name.endswith('.js'):
                    return os.path.join(patch_dir, dirs['js'], file_name)
                elif file_name.endswith(('.png', '.jpg', '.gif')):
                    return os.path.join(patch_dir, dirs['images'], file_name)
                elif file_name.endswith(('.woff', '.woff2', '.ttf')):
                    return os.path.join(patch_dir, dirs['fonts'], file_name)
                else:
                    return os.path.join(patch_dir, file_name)
        
        return os.path.join(patch_dir, file_name)

    def generate_code(self, task: CodeTask) -> GeneratedCode:
        """Generate code based on task description and requirements."""
        try:
            # Create a unique patch directory for this task
            patch_dir = self._get_patch_directory(task)
            
            # Create language-specific directories and config files
            self._create_language_directories(patch_dir, task.language)
            self._create_config_files(patch_dir, task)
            
            # Create prompt for code generation
            prompt = self._create_generation_prompt(task)
            
            # Generate code
            if self.client:
                # Use GPT-3.5 Turbo for code generation
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": """You are an expert programmer. Generate clean, efficient, and well-documented code.
                            Follow these rules:
                            1. Include proper type hints and docstrings
                            2. Add input validation where appropriate
                            3. Follow language-specific best practices
                            4. Include example usage in the main block
                            5. Generate test data and test cases
                            6. Return ONLY the implementation code, no markdown or explanation
                            7. NEVER include triple backticks (```) or language tags in your response
                            8. If the code processes files, ALWAYS include example input files
                            9. Add a run_example() function that demonstrates usage"""
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,  # Lower temperature for more focused generation
                    max_tokens=2000,
                    top_p=0.9,
                    frequency_penalty=0.0,
                    presence_penalty=0.0,
                    response_format={ "type": "text" }
                )
                
                # Get the generated code
                if response and response.choices:
                    code = response.choices[0].message.content.strip()
                    
                    # Clean the code
                    code = clean_code_document(code)
                    
                    # Create file path
                    safe_name = "".join(c if c.isalnum() else "_" for c in task.description.lower())
                    file_name = f"{safe_name[:50]}{self.LANGUAGE_EXTENSIONS.get(task.language.lower(), '.txt')}"
                    src_dir = os.path.join(patch_dir, "src")
                    file_path = os.path.join(src_dir, file_name)
                    
                    # Save the code
                    with open(file_path, "w") as f:
                        f.write(code)
                        
                    # Clean the file of backticks
                    clean_file_of_backticks(file_path)
                    
                    # Create metadata file
                    metadata = {
                        "description": task.description,
                        "language": task.language,
                        "requirements": task.requirements,
                        "created_at": task.created_at
                    }
                    
                    with open(os.path.join(patch_dir, "metadata.txt"), "w") as f:
                        json.dump(metadata, f, indent=2)
                    
                    # Generate test data if needed
                    if "csv" in task.description.lower() or "file" in task.description.lower():
                        test_data_prompt = f"""Generate example test data for this code. Requirements:
                        1. Task: {task.description}
                        2. Make it realistic but simple
                        3. Include edge cases
                        4. Return ONLY the test data content, no explanations
                        5. Format appropriately for the file type
                        6. Keep it small (3-5 records)"""
                        
                        test_data_response = self.client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are a data generation expert. Generate realistic test data."},
                                {"role": "user", "content": test_data_prompt}
                            ],
                            temperature=0.1,
                            max_tokens=500,
                            response_format={ "type": "text" }
                        )
                        
                        if test_data_response and test_data_response.choices:
                            test_data = test_data_response.choices[0].message.content.strip()
                            test_data_path = os.path.join(patch_dir, 'src', 'test_data.csv')
                            with open(test_data_path, 'w') as f:
                                f.write(test_data)
                    
                    return GeneratedCode(
                        content=code,
                        language=task.language,
                        file_path=os.path.join("project", os.path.relpath(file_path, self.project_dir)),
                        description=task.description,
                        created_at=datetime.now().isoformat()
                    )
                else:
                    raise Exception("No code generated from the API")
            else:
                raise ValueError("OpenAI client is not configured")
        except Exception as e:
            logger.error(f"Error generating code: {str(e)}")
            raise

    def save_code(self, generated_code: GeneratedCode) -> bool:
        """Save the generated code to file."""
        try:
            # Ensure the src directory exists
            os.makedirs(os.path.dirname(generated_code.file_path), exist_ok=True)
            
            # Save main code file
            with open(generated_code.file_path, 'w') as f:
                f.write(generated_code.content)
            
            return True
        except Exception as e:
            logger.error(f"Error saving code: {str(e)}")
            return False

    def run_tests(self, generated_code: GeneratedCode) -> Tuple[bool, str]:
        """Run the generated tests.
        
        This method supports two types of testing:
        1. Separate test files (e.g. pytest files)
        2. Inline tests (when the code has a __main__ block with tests)
        """
        try:
            if generated_code.language.lower() == "python":
                # First try running the file directly for inline tests
                main_file = generated_code.file_path
                process = subprocess.Popen(
                    [sys.executable, main_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=os.path.dirname(main_file)
                )
                output, error_output = process.communicate()
                
                # If the main file execution was successful, return its results
                if process.returncode == 0:
                    return True, output
                
                # If there are separate tests, try running those
                if generated_code.tests:
                    # Save tests temporarily
                    test_file = self._get_test_file_path(generated_code.file_path)
                    with open(test_file, 'w') as f:
                        f.write(generated_code.tests)
                    
                    # Run tests using pytest
                    result = subprocess.run(
                        ['pytest', test_file],
                        capture_output=True,
                        text=True
                    )
                    
                    success = result.returncode == 0
                    output = result.stdout if success else result.stderr
                    
                    return success, output
                
                # If main file execution failed and no separate tests exist
                return False, f"Execution failed:\nOutput: {output}\nError: {error_output}"
            
            # Add support for other languages' test runners
            return False, f"Testing not implemented for {generated_code.language}"
            
        except Exception as e:
            logger.error(f"Error running tests: {str(e)}")
            return False, str(e)

    def assess_output(self, output: str, error_output: str, task: CodeTask) -> tuple[bool, str, list[str]]:
        """Assess the execution output and determine if improvements are needed.
        
        Args:
            output: Standard output from code execution
            error_output: Standard error output from code execution
            task: Original code generation task
            
        Returns:
            tuple[bool, str, list[str]]: (needs_improvement, analysis, suggested_fixes)
        """
        try:
            if not self.client:
                return False, "OpenAI client not available", []

            # Create prompt for output analysis
            prompt = f"""
            Analyze the execution output of code generated for the following task:
            Description: {task.description}
            Language: {task.language}
            Requirements:
            {chr(10).join(f'- {req}' for req in task.requirements)}

            Standard Output:
            {output}

            Error Output:
            {error_output}

            Please analyze if the code needs improvements based on:
            1. Error messages or exceptions
            2. Incorrect output format or content
            3. Performance issues
            4. Missing functionality
            5. Best practices violations

            Provide your analysis and specific code improvements needed.
            """

            # Get analysis from OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a code review expert. Analyze code execution output and suggest specific improvements."},
                    {"role": "user", "content": prompt}
                ]
            )

            analysis = response.choices[0].message.content

            # Parse if improvements needed and specific fixes
            needs_improvement = any(indicator in analysis.lower() for indicator in [
                "error", "exception", "incorrect", "missing", "should", "could be improved",
                "recommend", "suggest", "better to", "needs to"
            ])

            # Extract specific fixes if improvements needed
            fixes = []
            if needs_improvement:
                # Get specific fixes from OpenAI
                fix_prompt = f"""
                Based on this analysis:
                {analysis}

                List specific code changes needed (one per line):
                """
                
                fix_response = self.client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": "You are a code improvement expert. List specific code changes needed."},
                        {"role": "user", "content": fix_prompt}
                    ]
                )
                
                fixes = [fix.strip() for fix in fix_response.choices[0].message.content.split('\n') if fix.strip()]

            return needs_improvement, analysis, fixes

        except Exception as e:
            logger.error(f"Error assessing output: {str(e)}")
            return False, f"Error in assessment: {str(e)}", []

    def improve_code(self, patch_dir: str, task: CodeTask, analysis: str, fixes: list[str]) -> bool:
        """Improve code based on execution analysis and suggested fixes.
        
        Args:
            patch_dir: Path to the patch directory
            task: Original code generation task
            analysis: Analysis of the execution output
            fixes: List of specific fixes needed
            
        Returns:
            bool: True if improvements were made successfully
        """
        try:
            if not self.client:
                return False

            # Find main source file
            src_dir = os.path.join(patch_dir, "src")
            source_files = [f for f in os.listdir(src_dir) if os.path.isfile(os.path.join(src_dir, f))]
            if not source_files:
                return False
            
            main_file = source_files[0]
            main_file_path = os.path.join(src_dir, main_file)

            # Read current code
            with open(main_file_path, 'r') as f:
                current_code = f.read()

            # Create prompt for code improvement
            prompt = f"""
            Improve this code based on execution analysis and suggested fixes:

            Current Code:
            {current_code}

            Task Description: {task.description}
            Language: {task.language}
            Requirements:
            {chr(10).join(f'- {req}' for req in task.requirements)}

            Analysis of Issues:
            {analysis}

            Needed Fixes:
            {chr(10).join(f'- {fix}' for fix in fixes)}

            Please provide the complete improved code that fixes these issues while maintaining the original functionality.
            """

            # Get improved code from OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a code improvement expert. Provide improved code that fixes identified issues."},
                    {"role": "user", "content": prompt}
                ]
            )

            improved_code = response.choices[0].message.content

            # Extract code block if present
            if "```" in improved_code:
                improved_code = improved_code.split("```")[1]
                if improved_code.startswith(task.language):
                    improved_code = improved_code[len(task.language):].strip()

            # Format the improved code
            improved_code = self._format_code(improved_code, task.language)

            # Save improved code
            with open(main_file_path, 'w') as f:
                f.write(improved_code)

            # Update metadata to reflect improvements
            metadata_path = os.path.join(patch_dir, "metadata.txt")
            with open(metadata_path, 'a') as f:
                f.write("\nImprovements Made:\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write("Analysis:\n")
                f.write(f"{analysis}\n")
                f.write("Fixes Applied:\n")
                for fix in fixes:
                    f.write(f"- {fix}\n")

            return True

        except Exception as e:
            logger.error(f"Error improving code: {str(e)}")
            return False

    def run_and_improve(self, patch_dir: str, task: CodeTask) -> tuple[bool, str]:
        """Run code and recursively improve it based on output.
        
        Args:
            patch_dir: Path to the patch directory
            task: Code generation task
            
        Returns:
            tuple[bool, str]: (success, final_output)
        """
        try:
            if not self.client:
                return False, "OpenAI client not initialized - check API key"

            attempts = 0
            while attempts < self.max_improvement_attempts:
                # Run the code
                process = subprocess.Popen(
                    [sys.executable, os.path.join(patch_dir, "src", os.listdir(os.path.join(patch_dir, "src"))[0])],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                output, error_output = process.communicate()

                # Check if the code execution was successful
                if process.returncode != 0:
                    return False, f"Code execution failed:\nOutput: {output}\nError: {error_output}"

                # Assess the output
                try:
                    needs_improvement, analysis, fixes = self.assess_output(output, error_output, task)
                except Exception as e:
                    if "invalid_api_key" in str(e):
                        return False, "Invalid OpenAI API key - please check your configuration"
                    return False, f"Error assessing code: {str(e)}"

                if not needs_improvement:
                    return True, f"Code execution successful:\n{output}"

                # Try to improve the code
                try:
                    if not self.improve_code(patch_dir, task, analysis, fixes):
                        return False, f"Failed to improve code after attempt {attempts + 1}"
                except Exception as e:
                    if "invalid_api_key" in str(e):
                        return False, "Invalid OpenAI API key - please check your configuration"
                    return False, f"Error improving code: {str(e)}"

                attempts += 1

            return False, f"Max improvement attempts ({self.max_improvement_attempts}) reached"

        except Exception as e:
            logger.error(f"Error in run and improve: {str(e)}")
            return False, str(e) 