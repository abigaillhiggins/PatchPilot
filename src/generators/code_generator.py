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
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import re

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
    
    This function uses a character-by-character parser to extract code between
    triple backtick markers (```python ... ```). It handles nested code blocks
    and ensures only the code content is preserved.
    
    Args:
        code: Raw code string that may contain markdown formatting
        
    Returns:
        Clean code string with markdown formatting removed
    """
    # Remove leading/trailing whitespace
    code = code.strip()
    
    # Initialize state variables
    result = []
    i = 0
    in_code_block = False
    backtick_count = 0
    found_first_block = False
    
    while i < len(code):
        char = code[i]
        
        # Handle backticks
        if char == '`':
            backtick_count += 1
            if backtick_count == 3:
                # We found a triple backtick
                if not in_code_block and not found_first_block:
                    # Start of first code block - check for python tag
                    python_tag_start = i + 1
                    while python_tag_start < len(code) and code[python_tag_start].isspace():
                        python_tag_start += 1
                    if code[python_tag_start:].startswith('python'):
                        i = python_tag_start + 6  # Skip 'python'
                    in_code_block = True
                    found_first_block = True
                elif in_code_block:
                    # End of code block
                    in_code_block = False
                    # If this was the first block, we're done
                    if found_first_block:
                        break
                backtick_count = 0
            i += 1
            continue
            
        # Reset backtick count if not consecutive
        if backtick_count > 0 and char != '`':
            # If we have incomplete backticks, treat them as regular characters
            for _ in range(backtick_count):
                if in_code_block:
                    result.append('`')
            backtick_count = 0
            
        # Collect code content
        if in_code_block:
            if backtick_count == 0:  # Only add if not part of closing backticks
                result.append(char)
        
        i += 1
    
    # Join and clean the result
    cleaned = ''.join(result).strip()
    
    # Handle case where no code blocks were found
    if not cleaned and not any(c == '`' for c in code):
        return code.strip()
    elif not cleaned:
        # Return original text if it has incomplete backticks
        return code.strip()
        
    return cleaned

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
    """Code generation and management class using Qwen2.5 autocoder."""

    LANGUAGE_EXTENSIONS = {
        'python': '.py',
        'javascript': '.js',
        'typescript': '.ts',
        'java': '.java',
        'cpp': '.cpp',
        'c': '.c',
        'go': '.go',
        'rust': '.rs'
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

    def __init__(self, project_dir: str = "."):
        """Initialize the code generator.
        
        Args:
            project_dir: Root directory of the project
        """
        self.project_dir = os.path.abspath(project_dir)
        self.patches_dir = os.path.join(self.project_dir, "patches")
        
        # Initialize Qwen2.5 model
        try:
            self.tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-7B", trust_remote_code=True)
            self.model = AutoModelForCausalLM.from_pretrained(
                "Qwen/Qwen2.5-Coder-7B",
                trust_remote_code=True,
                load_in_8bit=True,
                device_map="auto"
            )
            self.model = self.model.eval()
            logger.info("Qwen2.5-Coder model initialized successfully.")
        except Exception as e:
            self.model = None
            self.tokenizer = None
            logger.error(f"Failed to initialize Qwen2.5-Coder model: {str(e)}")
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

    def _create_language_directories(self, patch_dir: str, language: str):
        """Create language-specific directories in the patch directory."""
        os.makedirs(os.path.join(patch_dir, "src"), exist_ok=True)
        os.makedirs(os.path.join(patch_dir, "tests"), exist_ok=True)
        os.makedirs(os.path.join(patch_dir, "docs"), exist_ok=True)

    def _create_config_files(self, patch_dir: str, task: CodeTask):
        """Create necessary configuration files based on the language."""
        if task.language.lower() == 'python':
            # Create requirements.txt if package requirements exist
            if task.package_requirements:
                with open(os.path.join(patch_dir, "requirements.txt"), "w") as f:
                    f.write("\n".join(task.package_requirements))

    def _format_code(self, code: str, language: str) -> str:
        """Format the code according to language-specific standards."""
        try:
            if language.lower() == 'python':
                # Use black for Python code formatting
                code = black.format_str(code, mode=black.FileMode())
                # Additional PEP 8 formatting
                code = autopep8.fix_code(code)
            # Add formatters for other languages as needed
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

    def _create_generation_prompt(self, task: CodeTask) -> str:
        """Create a prompt for code generation based on the task.
        
        Args:
            task: The coding task to generate code for
            
        Returns:
            A formatted prompt string for the model
        """
        # Start with a clear instruction
        prompt = f"You are a professional software developer. Write {task.language} code that implements the following:\n\n"
        
        # Add the main task description
        prompt += f"Task: {task.description}\n\n"
        
        # Add requirements if any
        if task.requirements:
            prompt += "Requirements:\n"
            for req in task.requirements:
                prompt += f"- {req}\n"
            prompt += "\n"
            
        # Add package requirements if any
        if task.package_requirements:
            prompt += "Required packages:\n"
            for pkg in task.package_requirements:
                prompt += f"- {pkg}\n"
            prompt += "\n"
            
        # Add context if available
        if task.context:
            prompt += f"Additional context: {task.context}\n\n"
            
        # Add language-specific instructions
        if task.language.lower() == "python":
            prompt += "Write clean, well-documented Python code following PEP 8 style guidelines. Include docstrings and type hints.\n\n"
        elif task.language.lower() in ["javascript", "typescript"]:
            prompt += "Write clean, modern JavaScript/TypeScript code following standard style guidelines. Use ES6+ features where appropriate.\n\n"
        elif task.language.lower() == "java":
            prompt += "Write clean Java code following standard conventions. Include JavaDoc comments and proper exception handling.\n\n"
        elif task.language.lower() == "go":
            prompt += "Write idiomatic Go code following the official style guide. Include proper error handling and documentation.\n\n"
        elif task.language.lower() == "rust":
            prompt += "Write idiomatic Rust code following the official style guide. Include proper error handling and documentation.\n\n"
            
        # Request for code
        prompt += f"Please provide the complete {task.language} implementation:\n\n"
        
        return prompt

    def generate_code(self, task: CodeTask) -> GeneratedCode:
        """Generate code based on task description and requirements."""
        try:
            if not (self.model and self.tokenizer):
                raise ValueError("Qwen2.5 model not initialized")

            # Create a unique patch directory for this task
            patch_dir = self._get_patch_directory(task)
            
            # Create language-specific directories and config files
            self._create_language_directories(patch_dir, task.language)
            self._create_config_files(patch_dir, task)
            
            # Create prompt for code generation
            prompt = self._create_generation_prompt(task)
            
            # Generate code using Qwen2.5
            inputs = self.tokenizer(prompt, return_tensors="pt")
            if torch.cuda.is_available():
                inputs = inputs.to("cuda")
            
            # Generate with appropriate parameters
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=2048,
                temperature=0.2,
                top_p=0.95,
                top_k=50,
                repetition_penalty=1.1,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
            
            # Decode the generated code
            generated_code = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            code = generated_code[len(prompt):].strip()  # Remove the prompt from the output
            
            # Clean and format the code
            code = self._format_code(code, task.language)
            
            # Create file path
            safe_name = "".join(c if c.isalnum() else "_" for c in task.description.lower())
            file_name = f"{safe_name[:50]}{self.LANGUAGE_EXTENSIONS.get(task.language.lower(), '.txt')}"
            src_dir = os.path.join(patch_dir, "src")
            file_path = os.path.join(src_dir, file_name)
            
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
                
        except Exception as e:
            logger.error(f"Failed to generate code: {str(e)}")
            raise

    def save_code(self, generated_code: GeneratedCode) -> bool:
        """Save the generated code to file."""
        try:
            # Ensure the src directory exists
            os.makedirs(os.path.dirname(generated_code.file_path), exist_ok=True)
            
            # Get the content and normalize line endings
            content = generated_code.content.replace('\r\n', '\n')
            
            # Split content into lines
            lines = content.split('\n')
            cleaned_lines = []
            in_code_block = False
            found_first_block = False
            
            for line in lines:
                stripped = line.strip()
                
                # Handle code block markers
                if stripped == '```python' or stripped == '```':
                    if not found_first_block:
                        found_first_block = True
                        in_code_block = True
                    else:
                        in_code_block = False
                    continue
                
                # Skip lines before first code block
                if not found_first_block:
                    continue
                
                # Stop at explanation text
                if stripped.startswith('This '):
                    break
                
                # Only include lines inside code block
                if in_code_block:
                    cleaned_lines.append(line)
            
            # Join lines back together
            content = '\n'.join(cleaned_lines).strip()
            
            # Save main code file
            with open(generated_code.file_path, 'w') as f:
                f.write(content)
            
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
            if not (self.model and self.tokenizer):
                return False, "Qwen2.5 model not initialized", []

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

            # Generate analysis using Qwen2.5
            inputs = self.tokenizer(prompt, return_tensors="pt")
            if torch.cuda.is_available():
                inputs = inputs.to("cuda")
            
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=2048,
                temperature=0.2,
                top_p=0.95,
                top_k=50,
                repetition_penalty=1.1,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
            
            analysis = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            analysis = analysis[len(prompt):].strip()

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
                
                fix_inputs = self.tokenizer(fix_prompt, return_tensors="pt")
                if torch.cuda.is_available():
                    fix_inputs = fix_inputs.to("cuda")
                
                fix_outputs = self.model.generate(
                    **fix_inputs,
                    max_new_tokens=2048,
                    temperature=0.2,
                    top_p=0.95,
                    top_k=50,
                    repetition_penalty=1.1,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
                
                fixes = [fix.strip() for fix in self.tokenizer.decode(fix_outputs[0], skip_special_tokens=True)[len(fix_prompt):].strip().split('\n') if fix.strip()]

            return needs_improvement, analysis, fixes
        except Exception as e:
            logger.error(f"Error assessing output: {str(e)}")
            return False, f"Error in assessment: {str(e)}", []

    def improve_code(self, code: str, fixes: list[str], task: CodeTask) -> str:
        """Improve the code based on suggested fixes."""
        try:
            if not (self.model and self.tokenizer):
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
            Return ONLY the implementation code.
            """

            # Generate improved code using Qwen2.5
            inputs = self.tokenizer(prompt, return_tensors="pt")
            if torch.cuda.is_available():
                inputs = inputs.to("cuda")
            
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=2048,
                temperature=0.2,
                top_p=0.95,
                top_k=50,
                repetition_penalty=1.1,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
            
            # Decode and clean the improved code
            improved_code = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            improved_code = improved_code[len(prompt):].strip()
            
            # Format the improved code
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
            if not (self.model and self.tokenizer):
                return False, "Qwen2.5 model not initialized - check configuration"

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