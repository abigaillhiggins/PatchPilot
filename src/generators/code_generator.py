"""
Autonomous code generation module for PatchPilot.
This module provides functionality to generate, test, and manage code autonomously using Groq API for Qwen AutoCoder 2.5.
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
import groq
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
        
        # Initialize Groq API for Qwen2.5
        try:
            api_key = os.getenv('GROQ_API_KEY')
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable not set")
            
            self.client = groq.Groq(api_key=api_key)
            logger.info("Groq API initialized successfully for Qwen2.5-Coder.")
        except Exception as e:
            self.client = None
            logger.error(f"Failed to initialize Groq API for Qwen2.5-Coder: {str(e)}")
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
            prompt += (
                "Write clean, well-documented Python code following PEP 8 style guidelines. "
                "Include docstrings and type hints.\n"
                "ALSO, generate a requirements.txt file listing ALL external dependencies needed to run the code. "
                "Include ALL packages that need to be installed via pip (requests, beautifulsoup4, pandas, numpy, etc). "
                "Do NOT include standard library modules (os, sys, json, csv, argparse, logging, typing, etc). "
                "If no external dependencies are needed, generate an empty requirements.txt file. "
                "Output both the code and the requirements.txt file, clearly separated in markdown code blocks.\n"
                "IMPORTANT: When creating multiple files, use file paths in code block headers like ```main.py, ```requirements.txt, ```utils.py, etc.\n"
                "CRITICAL: The requirements.txt file should contain ONLY package names and versions, one per line. "
                "Do NOT include comments, Docker commands, or pip install commands.\n"
                "CRITICAL: The main.py file should contain ONLY Python code. Do NOT include project structure comments, "
                "file listings, or requirements.txt content in the main.py file.\n\n"
            )
            
            # Add startApp compatibility instructions for web applications
            if self._is_web_application_task(task):
                prompt += self._get_web_app_compatibility_instructions()
                
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

    def _is_web_application_task(self, task: CodeTask) -> bool:
        """Detect if the task is for a web application based on description and requirements."""
        web_keywords = [
            'web', 'website', 'webapp', 'web app', 'flask', 'django', 'fastapi', 'streamlit', 'dash',
            'server', 'api', 'rest', 'http', 'browser', 'frontend', 'backend', 'ui', 'interface',
            'calculator', 'dashboard', 'form', 'html', 'css', 'javascript', 'react', 'vue', 'angular',
            'gui', 'graphical', 'user interface', 'web interface', 'online', 'web-based'
        ]
        
        description_lower = task.description.lower()
        requirements_lower = ' '.join(task.requirements).lower()
        
        # Check description for web keywords
        for keyword in web_keywords:
            if keyword in description_lower:
                return True
                
        # Check requirements for web keywords
        for keyword in web_keywords:
            if keyword in requirements_lower:
                return True
                
        # Check for specific web frameworks in package requirements
        web_frameworks = ['flask', 'django', 'fastapi', 'streamlit', 'dash', 'bottle', 'tornado']
        for framework in web_frameworks:
            if framework in task.package_requirements:
                return True
                
        return False

    def _get_web_app_compatibility_instructions(self) -> str:
        """Get specific instructions for web application compatibility with startApp."""
        return """
=== WEB APPLICATION COMPATIBILITY REQUIREMENTS ===

If this is a web application, follow these CRITICAL requirements for startApp compatibility:

1. PORT CONFIGURATION:
   - Use environment variable for port: port = int(os.environ.get('PORT', 5001))
   - Default to port 5001 to avoid macOS AirPlay conflicts
   - Use host='0.0.0.0' for external access
   - Example: app.run(debug=True, host='0.0.0.0', port=port)

2. FLASK APPLICATIONS:
   - Create proper templates/ directory structure
   - Place HTML templates in src/templates/ directory
   - Use render_template() for serving HTML pages
   - Include proper error handling and form processing
   - Add a health check endpoint: @app.route('/health')

3. TEMPLATE STRUCTURE:
   - Create src/templates/ directory
   - Use modern, responsive HTML with CSS styling
   - Include proper form handling and validation
   - Add user-friendly error messages and success feedback

4. REQUIREMENTS.TXT:
   - Include flask>=2.0.0 for Flask applications
   - Include all necessary dependencies
   - Use proper version specifications

5. MAIN ENTRY POINT:
   - Ensure main.py can be run directly: python main.py
   - Include proper if __name__ == '__main__': block
   - Add proper logging and error handling

6. FILE STRUCTURE:
   ```
   src/
   ├── main.py
   ├── templates/
   │   └── index.html
   └── static/ (if needed)
   requirements.txt
   metadata.txt
   ```

7. EXAMPLE FLASK STRUCTURE:
   ```python
   from flask import Flask, render_template, request, jsonify
   import os
   
   app = Flask(__name__)
   
   @app.route('/')
   def index():
       return render_template('index.html')
   
   @app.route('/health')
   def health():
       return jsonify({'status': 'healthy'})
   
   if __name__ == '__main__':
       port = int(os.environ.get('PORT', 5001))
       app.run(debug=True, host='0.0.0.0', port=port)
   ```

CRITICAL: Follow these requirements exactly to ensure startApp compatibility!
"""

    def _create_simplified_prompt(self, task: CodeTask) -> str:
        """Create a simplified prompt for complex tasks that failed initial generation."""
        # Extract the core requirement from the task description
        description = task.description
        
        # For very long descriptions, extract the main requirement
        if len(description) > 300:
            # Try to find the main action (usually after "Create" or "Build")
            import re
            match = re.search(r'(?:Create|Build|Make|Develop)\s+([^,]+)', description, re.IGNORECASE)
            if match:
                core_requirement = match.group(1).strip()
            else:
                # Fallback: take first sentence
                core_requirement = description.split('.')[0]
        else:
            core_requirement = description
        
        simplified_prompt = f"""Create a Python implementation for: {core_requirement}

Focus on the core functionality. Generate clean, well-documented code with proper error handling.
Include a requirements.txt file listing ALL external dependencies needed (requests, beautifulsoup4, pandas, etc).
Do NOT include standard library modules (os, sys, json, csv, argparse, logging, typing, etc).
The requirements.txt should contain ONLY package names and versions, one per line.

Output the code in markdown code blocks."""
        
        return simplified_prompt

    def generate_code(self, task: CodeTask) -> GeneratedCode:
        """Generate code based on task description and requirements."""
        try:
            if not self.client:
                raise ValueError("Groq API client not initialized")

            # Create a unique patch directory for this task
            patch_dir = self._get_patch_directory(task)
            
            # Create language-specific directories and config files
            self._create_language_directories(patch_dir, task.language)
            self._create_config_files(patch_dir, task)
            
            # Create prompt for code generation
            prompt = self._create_generation_prompt(task)
            
            # Generate code using Groq API
            response = self.client.chat.completions.create(
                model="qwen/qwen3-32b",
                messages=[
                    {"role": "system", "content": "You are an expert programmer. Generate clean, efficient, and well-documented code."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=8192,  # Increased from 2048 to handle complex projects
                temperature=0.2,
                top_p=0.95
            )
            
            # Decode the generated code
            raw_response = response.choices[0].message.content
            raw_response = raw_response.strip()  # Remove the prompt from the output
            
            # Log token usage for monitoring
            if hasattr(response, 'usage'):
                logger.info(f"Token usage - Input: {response.usage.prompt_tokens}, Output: {response.usage.completion_tokens}, Total: {response.usage.total_tokens}")
            else:
                logger.info(f"Response length: {len(raw_response)} characters")
            
            # Validate response completeness
            if len(raw_response) < 50:  # Very short responses are likely truncated
                logger.warning(f"Response seems truncated (length: {len(raw_response)})")
                # Retry with simplified prompt for complex tasks
                if len(task.description) > 200:
                    logger.info("Retrying with simplified prompt")
                    simplified_prompt = self._create_simplified_prompt(task)
                    response = self.client.chat.completions.create(
                        model="qwen/qwen3-32b",
                        messages=[
                            {"role": "system", "content": "You are an expert programmer. Generate clean, efficient, and well-documented code."},
                            {"role": "user", "content": simplified_prompt}
                        ],
                        max_tokens=8192,
                        temperature=0.2,
                        top_p=0.95
                    )
                    raw_response = response.choices[0].message.content.strip()
            
            # Extract multiple files from the response
            extracted_files = self._extract_files_from_response(raw_response)
            
            if not extracted_files:
                raise Exception("No code files could be extracted from the response")
            
            # Get the main code file (prioritize main.py, then any .py file, then first file)
            main_code = None
            main_file_name = None
            
            if 'main.py' in extracted_files:
                main_code = extracted_files['main.py']
                main_file_name = 'main.py'
            else:
                # Find any Python file
                for file_name, content in extracted_files.items():
                    if file_name.endswith('.py'):
                        main_code = content
                        main_file_name = file_name
                        break
                
                # If no Python file found, use the first file
                if not main_code and extracted_files:
                    main_file_name = list(extracted_files.keys())[0]
                    main_code = extracted_files[main_file_name]
            
            # Clean and format the main code
            main_code = self._format_code(main_code, task.language)
            
            # Create file path for main code
            src_dir = os.path.join(patch_dir, "src")
            file_path = os.path.join(src_dir, main_file_name)
            
            # Create GeneratedCode object
            generated_code = GeneratedCode(
                content=main_code,
                language=task.language,
                file_path=file_path,
                description=task.description
            )
            
            # Save all files
            if self.save_multiple_files(extracted_files, patch_dir):
                return generated_code
            else:
                raise Exception("Failed to save generated files")
                
        except Exception as e:
            logger.error(f"Failed to generate code: {str(e)}")
            raise

    def _extract_files_from_response(self, content: str) -> dict:
        """Extract multiple files from Groq API response.
        
        Returns:
            dict: Dictionary with file names as keys and file contents as values
        """
        import re
        
        # Remove <think> tags and their content
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
        content = re.sub(r'<think>', '', content)
        content = re.sub(r'</think>', '', content)
        
        files = {}
        
        # Find all code blocks with file paths or language tags
        # This regex matches both ```filename.ext and ```language patterns
        code_blocks = re.findall(r'```([^\n]+)\n(.*?)```', content, re.DOTALL)
        
        for block in code_blocks:
            header, code_content = block
            code_content = code_content.strip()
            
            # Parse the header to determine file name and language
            header_parts = header.strip().split('/')
            
            if len(header_parts) > 1:
                # This is a file path like "backend/main.py" or "frontend/app.js"
                file_name = header_parts[-1]  # Get the filename part
                files[file_name] = code_content
            else:
                # This is a language tag like "python" or "javascript"
                language = header_parts[0].lower()
                
                # Determine file name based on language and content
                if language == 'txt' or 'requirements' in code_content.lower():
                    # This is likely a requirements.txt file
                    files['requirements.txt'] = code_content
                elif language == 'python' or language == 'py':
                    # This is Python code - use as main file
                    files['main.py'] = code_content
                elif language == 'javascript' or language == 'js':
                    files['main.js'] = code_content
                elif language == 'typescript' or language == 'ts':
                    files['main.ts'] = code_content
                elif language == 'html':
                    files['index.html'] = code_content
                elif language == 'css':
                    files['style.css'] = code_content
                elif language == 'json':
                    files['config.json'] = code_content
                elif language:
                    # Other language files
                    files[f'main.{language}'] = code_content
                else:
                    # No language specified, assume it's the main code file
                    if 'requirements.txt' not in files:
                        files['main.py'] = code_content
        
        # If no files were extracted, try to extract just the main code
        if not files:
            # Fallback to old method for backward compatibility
            main_code = self._extract_main_code_only(content)
            if main_code:
                files['main.py'] = main_code
        
        # Post-process files to clean up common issues
        files = self._clean_extracted_files(files)
        
        return files
    
    def _clean_extracted_files(self, files: dict) -> dict:
        """Clean up extracted files to fix common issues."""
        import re
        
        cleaned_files = {}
        
        for file_name, content in files.items():
            if file_name == 'main.py':
                # Clean main.py of project structure comments and requirements.txt content
                lines = content.split('\n')
                cleaned_lines = []
                skip_until_code = False
                
                for line in lines:
                    stripped = line.strip()
                    
                    # Skip project structure comments
                    if (stripped.startswith('# Project structure') or 
                        stripped.startswith('# requirements.txt') or
                        stripped.startswith('scraper_project/') or
                        stripped.startswith('├──') or
                        stripped.startswith('└──') or
                        stripped.startswith('│') or
                        stripped.startswith('requirements') and 'requests' in line):
                        continue
                    
                    # Skip empty lines after project structure
                    if skip_until_code and not stripped:
                        continue
                    
                    # If we find actual Python code, stop skipping
                    if (stripped.startswith('import ') or 
                        stripped.startswith('from ') or 
                        stripped.startswith('def ') or 
                        stripped.startswith('class ') or
                        stripped.startswith('if __name__')):
                        skip_until_code = False
                    
                    # If we find a comment that looks like it's about project structure, skip until we find code
                    if stripped.startswith('#') and ('structure' in stripped.lower() or 'project' in stripped.lower()):
                        skip_until_code = True
                        continue
                    
                    if not skip_until_code:
                        cleaned_lines.append(line)
                
                # Join lines and clean up
                cleaned_content = '\n'.join(cleaned_lines).strip()
                if cleaned_content:
                    cleaned_files[file_name] = cleaned_content
            else:
                cleaned_files[file_name] = content
        
        return cleaned_files
    
    def _extract_main_code_only(self, content: str) -> str:
        """Extract only the main code (fallback method)."""
        import re
        
        lines = content.split('\n')
        cleaned_lines = []
        in_code_block = False
        found_first_block = False
        
        for line in lines:
            stripped = line.strip()
            
            # Handle code block markers
            if stripped.startswith('```'):
                if not found_first_block:
                    found_first_block = True
                    in_code_block = True
                else:
                    in_code_block = False
                continue
            
            # Skip lines before first code block
            if not found_first_block:
                continue
            
            # Stop at explanation text or key features
            if (stripped.startswith('### Key Features:') or 
                stripped.startswith('### Usage Instructions:') or
                stripped.startswith('This ') or
                stripped.startswith('The script uses')):
                break
            
            # Only include lines inside code block
            if in_code_block:
                cleaned_lines.append(line)
        
        # Join lines back together and clean up
        content = '\n'.join(cleaned_lines).strip()
        content = re.sub(r'```\s*$', '', content)
        
        return content

    def save_multiple_files(self, files: dict, patch_dir: str) -> bool:
        """Save multiple files to the patch directory."""
        try:
            # Clean the files first
            cleaned_files = self._clean_extracted_files(files)
            
            # Save each file
            for file_path, content in cleaned_files.items():
                full_path = os.path.join(patch_dir, file_path)
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Write the file
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
            # Post-generation enhancement for web applications
            self._enhance_web_app_compatibility(patch_dir, cleaned_files)
            
            logger.info(f"Successfully saved {len(cleaned_files)} files to {patch_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving multiple files: {str(e)}")
            return False

    def _enhance_web_app_compatibility(self, patch_dir: str, files: dict) -> None:
        """Enhance generated web applications to ensure startApp compatibility."""
        try:
            # Check if this is a web application
            if not self._is_web_app_directory(patch_dir, files):
                return
                
            logger.info(f"Enhancing web app compatibility for {patch_dir}")
            
            # Enhance main.py for proper port configuration
            self._enhance_main_py(patch_dir)
            
            # Ensure proper template structure
            self._ensure_template_structure(patch_dir)
            
            # Enhance requirements.txt
            self._enhance_requirements_txt(patch_dir)
            
            logger.info(f"Web app compatibility enhancement completed for {patch_dir}")
            
        except Exception as e:
            logger.error(f"Error enhancing web app compatibility: {str(e)}")

    def _is_web_app_directory(self, patch_dir: str, files: dict) -> bool:
        """Check if the generated code is a web application."""
        # Check for Flask/Django/FastAPI imports in main.py
        main_py_path = os.path.join(patch_dir, "src", "main.py")
        if os.path.exists(main_py_path):
            try:
                with open(main_py_path, 'r') as f:
                    content = f.read().lower()
                    web_frameworks = ['flask', 'django', 'fastapi', 'streamlit', 'dash']
                    for framework in web_frameworks:
                        if framework in content:
                            return True
            except Exception:
                pass
                
        # Check for web-related files
        web_files = ['templates', 'static', 'index.html', 'app.py', 'server.py']
        for file_path in files.keys():
            for web_file in web_files:
                if web_file in file_path.lower():
                    return True
                    
        return False

    def _enhance_main_py(self, patch_dir: str) -> None:
        """Enhance main.py for proper port configuration and startApp compatibility."""
        main_py_path = os.path.join(patch_dir, "src", "main.py")
        if not os.path.exists(main_py_path):
            return
            
        try:
            with open(main_py_path, 'r') as f:
                content = f.read()
                
            # Check if it's a Flask app
            if 'flask' in content.lower() and 'app.run(' in content:
                # Replace port configuration
                import re
                
                # Replace any hardcoded port with environment variable
                content = re.sub(
                    r'app\.run\([^)]*port\s*=\s*\d+[^)]*\)',
                    "app.run(debug=True, host='0.0.0.0', port=port)",
                    content
                )
                
                # Add port import if not present
                if 'import os' not in content:
                    content = content.replace('from flask import', 'import os\nfrom flask import')
                elif 'import os' in content and 'port = int(os.environ.get(' not in content:
                    # Add port configuration before app.run
                    content = re.sub(
                        r'(if __name__ == [\'"]__main__[\'"]:)',
                        r'\1\n    port = int(os.environ.get(\'PORT\', 5001))',
                        content
                    )
                
                # Add health check endpoint if not present
                if '@app.route(\'/health\')' not in content:
                    health_endpoint = '''
@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'message': 'Flask app is running!'})
'''
                    # Insert before the if __name__ block
                    content = re.sub(
                        r'(if __name__ == [\'"]__main__[\'"]:)',
                        f'{health_endpoint}\n\\1',
                        content
                    )
                    
                    # Add jsonify import if not present
                    if 'jsonify' not in content and 'from flask import' in content:
                        content = re.sub(
                            r'from flask import ([^)]+)',
                            r'from flask import \1, jsonify',
                            content
                        )
                
                # Write enhanced content
                with open(main_py_path, 'w') as f:
                    f.write(content)
                    
                logger.info(f"Enhanced main.py for startApp compatibility in {patch_dir}")
                
        except Exception as e:
            logger.error(f"Error enhancing main.py: {str(e)}")

    def _ensure_template_structure(self, patch_dir: str) -> None:
        """Ensure proper template structure for Flask applications."""
        src_dir = os.path.join(patch_dir, "src")
        templates_dir = os.path.join(src_dir, "templates")
        
        # Create templates directory if it doesn't exist
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir, exist_ok=True)
            
        # Check if there are HTML files in src directory that should be moved to templates
        if os.path.exists(src_dir):
            for file in os.listdir(src_dir):
                if file.endswith('.html') and file != 'templates':
                    src_file = os.path.join(src_dir, file)
                    template_file = os.path.join(templates_dir, file)
                    
                    # Move HTML files to templates directory
                    if not os.path.exists(template_file):
                        import shutil
                        shutil.move(src_file, template_file)
                        logger.info(f"Moved {file} to templates directory in {patch_dir}")

    def _enhance_requirements_txt(self, patch_dir: str) -> None:
        """Enhance requirements.txt to ensure Flask is included."""
        requirements_path = os.path.join(patch_dir, "requirements.txt")
        
        try:
            if os.path.exists(requirements_path):
                with open(requirements_path, 'r') as f:
                    content = f.read()
                    
                # Check if Flask is already included
                if 'flask' not in content.lower():
                    # Add Flask to requirements
                    flask_line = 'flask>=2.0.0\n'
                    with open(requirements_path, 'a') as f:
                        f.write(flask_line)
                    logger.info(f"Added Flask to requirements.txt in {patch_dir}")
            else:
                # Create requirements.txt with Flask
                with open(requirements_path, 'w') as f:
                    f.write('flask>=2.0.0\n')
                logger.info(f"Created requirements.txt with Flask in {patch_dir}")
                
        except Exception as e:
            logger.error(f"Error enhancing requirements.txt: {str(e)}")

    def save_code(self, generated_code: GeneratedCode) -> bool:
        """Save the generated code to file (legacy method)."""
        try:
            # Ensure the src directory exists
            os.makedirs(os.path.dirname(generated_code.file_path), exist_ok=True)
            
            # Save main code file (content is already cleaned in generate_code)
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
        """Assess the execution output and determine if improvements are needed."""
        try:
            if not self.client:
                return False, "Groq API client not initialized", []

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

            # Generate analysis using Groq API
            response = self.client.chat.completions.create(
                model="qwen/qwen3-32b",
                messages=[
                    {"role": "system", "content": "You are an expert code reviewer. Analyze code execution output and provide specific improvement suggestions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2048,
                temperature=0.2,
                top_p=0.95
            )
            
            analysis = response.choices[0].message.content
            analysis = analysis.strip()

            # Parse if improvements needed and specific fixes
            needs_improvement = any(indicator in analysis.lower() for indicator in [
                "error", "exception", "incorrect", "missing", "should", "could be improved",
                "recommend", "suggest", "better to", "needs to"
            ])

            # Extract specific fixes if improvements needed
            fixes = []
            if needs_improvement:
                # Get specific fixes from Groq API
                fix_prompt = f"""
                Based on this analysis:
                {analysis}

                List specific code changes needed (one per line):
                """
                
                response = self.client.chat.completions.create(
                    model="qwen/qwen3-32b",
                    messages=[
                        {"role": "system", "content": "You are an expert code reviewer. Provide specific, actionable code improvement suggestions."},
                        {"role": "user", "content": fix_prompt}
                    ],
                    max_tokens=2048,
                    temperature=0.2,
                    top_p=0.95
                )
                
                fixes = [fix.strip() for fix in response.choices[0].message.content.strip().split('\n') if fix.strip()]

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
            CRITICAL: Return ONLY the raw Python code without any explanations, markdown formatting, or code blocks.
            Do not include any triple backticks (```) or language tags.
            """

            # Generate improved code using Groq API
            response = self.client.chat.completions.create(
                model="qwen/qwen3-32b",
                messages=[
                    {"role": "system", "content": "You are an expert programmer. Improve the given code based on the specified requirements."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2048,
                temperature=0.2,
                top_p=0.95
            )
            
            # Decode and clean the improved code
            improved_code = response.choices[0].message.content
            improved_code = improved_code.strip()
            
            # Remove <think> tags and their content
            import re
            improved_code = re.sub(r'<think>.*?</think>', '', improved_code, flags=re.DOTALL)
            improved_code = re.sub(r'<think>', '', improved_code)
            improved_code = re.sub(r'</think>', '', improved_code)
            
            # Extract only the code part if it's wrapped in code blocks
            code_blocks = re.findall(r'```(?:python)?\n(.*?)```', improved_code, re.DOTALL)
            if code_blocks:
                improved_code = code_blocks[0].strip()
            
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
            if not self.client:
                return False, "Groq API client not initialized - check configuration"

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
                        return False, "Invalid Groq API key - please check your configuration"
                    return False, f"Error assessing code: {str(e)}"

                if not needs_improvement:
                    return True, f"Code execution successful:\n{output}"

                # Try to improve the code
                try:
                    if not self.improve_code(output, fixes, task):
                        return False, f"Failed to improve code after attempt {attempts + 1}"
                except Exception as e:
                    if "invalid_api_key" in str(e):
                        return False, "Invalid Groq API key - please check your configuration"
                    return False, f"Error improving code: {str(e)}"

                attempts += 1

            return False, f"Max improvement attempts ({self.max_improvement_attempts}) reached"

        except Exception as e:
            logger.error(f"Error in run and improve: {str(e)}")
            return False, str(e) 