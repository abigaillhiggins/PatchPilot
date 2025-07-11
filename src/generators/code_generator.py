"""
Autonomous code generation module for PatchPilot.
This module provides functionality to generate, test, and manage code autonomously.
"""

import os
import logging
import subprocess
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import requests
import ast
import black
import autopep8
import shutil
import sys
import json
from openai import OpenAI

logger = logging.getLogger(__name__)

@dataclass
class CodeTask:
    """Represents a coding task with requirements and context."""
    description: str
    language: str
    requirements: List[str]  # Task requirements/features
    package_requirements: List[str] = field(default_factory=list)  # Actual Python package dependencies
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
        """Initialize the code generator.
        
        Args:
            api_key: OpenAI API key
            project_dir: Root directory of the project
        """
        self.api_key = api_key
        self.project_dir = os.path.abspath(project_dir)
        self.patches_dir = os.path.join(self.project_dir, "patches")
        
        # Validate API key
        if not (api_key and len(api_key) > 40 and api_key.startswith('sk-')):
            raise ValueError("Invalid OpenAI API key format")

        # Initialize OpenAI client
        try:
            self.client = OpenAI(api_key=api_key)
            # Test the client with a minimal API call
            self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "Test"}, {"role": "user", "content": "Test"}],
                max_tokens=1
            )
            logger.info("OpenAI API key validated successfully.")
        except Exception as e:
            self.client = None
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            logger.warning("Code generation and analysis features will be disabled.")
            
        self.max_improvement_attempts = 3
        self._ensure_directories_exist()

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
        """Create basic requirements.txt file with validated package requirements."""
        if task.language.lower() == 'python':
            with open(os.path.join(patch_dir, 'requirements.txt'), 'w') as f:
                f.write("# Python dependencies\n")
                
                # Add core testing package
                f.write("pytest>=7.0.0\n")
                
                # Add task-specific package requirements
                for req in task.package_requirements:
                    # Basic validation of package name format
                    if not any(char in req for char in ['<', '>', '=', ' ']):
                        # If no version specifier, add latest version
                        f.write(f"{req}>=1.0.0\n")
                    else:
                        # If requirement already has version specifier, use as is
                        f.write(f"{req}\n")
            
            # Store task requirements in a separate metadata file
            metadata = {
                "description": task.description,
                "language": task.language,
                "task_requirements": task.requirements,
                "context": task.context,
                "created_at": task.created_at
            }
            with open(os.path.join(patch_dir, "metadata.json"), 'w') as f:
                json.dump(metadata, f, indent=2)

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
            
            # Generate code using OpenAI's API
            if self.client:
                # Use OpenAI API for code generation
                try:
                    response = self.client.chat.completions.create(
                        model="gpt-4-turbo-preview",
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
                        ]
                    )
                except Exception as api_error:
                    logger.error(f"API call failed with error: {str(api_error)}")
                    raise
                
                # Get the generated code
                code = response.choices[0].message.content.strip()
                
                # Clean the code
                code = clean_code_document(code)
                
                # Create file path
                safe_name = "".join(c if c.isalnum() else "_" for c in task.description.lower())
                file_name = f"{safe_name[:50]}{self.LANGUAGE_EXTENSIONS.get(task.language.lower(), '.txt')}"
                src_dir = os.path.join(patch_dir, "src")
                file_path = os.path.join(src_dir, file_name)
                
                # Format the code
                code = self._format_code(code, task.language)
                
                # Create GeneratedCode object
                generated_code = GeneratedCode(
                    content=code,
                    language=task.language,
                    file_path=file_path,
                    description=task.description
                )
                
                # Save the code
                if self.save_code(generated_code):
                    return generated_code
                else:
                    raise Exception("Failed to save generated code")
            else:
                raise ValueError("API key not provided")
                
        except Exception as e:
            logger.error(f"Failed to generate code: {str(e)}")
            raise

    def save_code(self, generated_code: GeneratedCode) -> bool:
        """Save the generated code to file."""
        try:
            # Construct the full file path
            file_path = os.path.join(self.patches_dir, generated_code.file_path)
            
            # Ensure the src directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save main code file
            with open(file_path, 'w') as f:
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
        """Assess the execution output and determine if improvements are needed."""
        try:
            if not self.client:
                return False, "OpenAI API key not available", []

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

            analysis = response.choices[0].message.content.strip()

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

    def improve_code(self, code: str, fixes: list[str], task: CodeTask) -> str:
        """Improve the code based on suggested fixes."""
        try:
            if not self.client:
                return code

            # Create prompt for code improvement
            prompt = f"""
            Original code:
            {code}

            Required improvements:
            {chr(10).join(f'- {fix}' for fix in fixes)}

            Task description: {task.description}
            Language: {task.language}
            Requirements:
            {chr(10).join(f'- {req}' for req in task.requirements)}

            Please provide the improved code that addresses all the required improvements.
            Return ONLY the implementation code, no markdown or explanation.
            """

            # Get improved code from OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert programmer. Improve the code while maintaining its core functionality.
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
                ]
            )

            improved_code = response.choices[0].message.content.strip()
            
            # Clean and format the improved code
            improved_code = clean_code_document(improved_code)
            improved_code = self._format_code(improved_code, task.language)
            
            return improved_code
        except Exception as e:
            logger.error(f"Error improving code: {str(e)}")
            return code

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
                return False, "OpenAI API key not initialized - check configuration"

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
                    if not self.improve_code(output, fixes, task):
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