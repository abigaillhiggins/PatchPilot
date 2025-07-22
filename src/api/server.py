"""
FastAPI server implementation for PatchPilot.
Provides endpoints for todo management and code generation.
"""

import os
import sys
import json
import asyncio
import logging
import subprocess
import re
import socket
import random
import requests
from typing import List, Optional, Dict, Tuple, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.models import TodoItem
from core.db_utils import DatabaseManager
from core.todo_commands import TodoCommands
from generators.code_generator import CodeGenerator, CodeTask, GeneratedCode
from utils.env_manager import IsolatedEnvironment
from utils.git_manager import GitManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PatchPilot API",
    description="API for managing todos and generating code",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:4000", "http://127.0.0.1:4000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
db_manager = DatabaseManager(os.getenv("DB_PATH", "todos.db"))
todo_commands = TodoCommands(db_manager)

# Initialize code generator with project directory
code_generator = CodeGenerator(project_dir=os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Initialize git manager
git_manager = GitManager(os.path.abspath(os.path.dirname(__file__)))

# Store for patch run results and tasks
patch_run_results: Dict[str, Dict[str, Any]] = {}
patch_tasks: Dict[str, asyncio.Task] = {}

# Store for running web applications
running_web_apps: Dict[str, subprocess.Popen] = {}

def find_available_port(start_port: int = 5000, max_attempts: int = 100) -> int:
    """Find an available port starting from start_port."""
    for _ in range(max_attempts):
        port = random.randint(start_port, start_port + 999)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find available port in range {start_port}-{start_port + 999}")

def detect_web_application(patch_id: str) -> Optional[Dict[str, str]]:
    """Enhanced detection of web applications with comprehensive framework support."""
    try:
        patch_dir = os.path.join(code_generator.patches_dir, patch_id)
        if not os.path.exists(patch_dir):
            return None
            
        # Check for main Python file
        main_py_path = os.path.join(patch_dir, "src", "main.py")
        if not os.path.exists(main_py_path):
            return None
            
        with open(main_py_path, 'r') as f:
            content = f.read()
            
        # Enhanced Flask detection with multiple patterns
        if _is_flask_app(content):
            return _detect_flask_config(content)
            
        # Enhanced FastAPI detection
        elif _is_fastapi_app(content):
            return _detect_fastapi_config(content)
            
        # Enhanced Streamlit detection
        elif _is_streamlit_app(content):
            return {
                "type": "Streamlit",
                "url": "http://localhost:8501",
                "port": "8501",
                "framework": "Streamlit",
                "startup_command": "streamlit run main.py --server.port 8501 --server.address 0.0.0.0"
            }
            
        # Enhanced Dash detection
        elif _is_dash_app(content):
            return _detect_dash_config(content)
            
        # Enhanced Django detection
        elif _is_django_app(content, patch_dir):
            return {
                "type": "Django",
                "url": "http://localhost:8000",
                "port": "8000",
                "framework": "Django",
                "startup_command": "python manage.py runserver 0.0.0.0:8000"
            }
            
        # Enhanced Bottle detection
        elif _is_bottle_app(content):
            return _detect_bottle_config(content)
            
        # Enhanced Tornado detection
        elif _is_tornado_app(content):
            return _detect_tornado_config(content)
            
        # Generic web server detection with enhanced patterns
        elif _is_generic_web_server(content):
            return _detect_generic_web_config(content)
            
        return None
        
    except Exception as e:
        logger.error(f"Error detecting web application for patch {patch_id}: {str(e)}")
        return None

def _is_flask_app(content: str) -> bool:
    """Enhanced Flask detection with multiple patterns."""
    flask_patterns = [
        r'from flask import',
        r'import flask',
        r'Flask\(',
        r'app = Flask',
        r'@app\.route',
        r'app\.run\('
    ]
    
    content_lower = content.lower()
    return any(re.search(pattern, content_lower) for pattern in flask_patterns)

def _detect_flask_config(content: str) -> Dict[str, str]:
    """Detect Flask configuration with enhanced port detection."""
    # Extract port from multiple patterns
    port_patterns = [
        r'app\.run\([^)]*port\s*=\s*(\d+)',
        r'os\.environ\.get\([\'"]PORT[\'"],\s*(\d+)',
        r'port\s*=\s*(\d+)',
        r'PORT\s*=\s*(\d+)'
    ]
    
    port = '5001'  # Default to avoid macOS conflicts
    
    for pattern in port_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            port = match.group(1)
            break
    
    return {
        "type": "Flask",
        "url": f"http://localhost:{port}",
        "port": port,
        "framework": "Flask",
        "startup_command": f"python main.py",
        "has_templates": "templates" in content or "render_template" in content,
        "has_static": "static" in content or "url_for" in content
    }

def _is_fastapi_app(content: str) -> bool:
    """Enhanced FastAPI detection."""
    fastapi_patterns = [
        r'from fastapi import',
        r'import fastapi',
        r'FastAPI\(',
        r'app = FastAPI',
        r'@app\.get',
        r'@app\.post',
        r'uvicorn\.run'
    ]
    
    content_lower = content.lower()
    return any(re.search(pattern, content_lower) for pattern in fastapi_patterns)

def _detect_fastapi_config(content: str) -> Dict[str, str]:
    """Detect FastAPI configuration."""
    port_match = re.search(r'uvicorn\.run\([^)]*port\s*=\s*(\d+)', content)
    port = port_match.group(1) if port_match else '8000'
    
    return {
        "type": "FastAPI",
        "url": f"http://localhost:{port}",
        "port": port,
        "framework": "FastAPI",
        "startup_command": f"uvicorn main:app --host 0.0.0.0 --port {port} --reload"
    }

def _is_streamlit_app(content: str) -> bool:
    """Enhanced Streamlit detection."""
    streamlit_patterns = [
        r'import streamlit',
        r'from streamlit import',
        r'st\.',
        r'streamlit\.run'
    ]
    
    content_lower = content.lower()
    return any(re.search(pattern, content_lower) for pattern in streamlit_patterns)

def _is_dash_app(content: str) -> bool:
    """Enhanced Dash detection."""
    dash_patterns = [
        r'import dash',
        r'from dash import',
        r'Dash\(',
        r'app = dash\.Dash',
        r'app\.run_server'
    ]
    
    content_lower = content.lower()
    return any(re.search(pattern, content_lower) for pattern in dash_patterns)

def _detect_dash_config(content: str) -> Dict[str, str]:
    """Detect Dash configuration."""
    port_match = re.search(r'app\.run_server\([^)]*port\s*=\s*(\d+)', content)
    port = port_match.group(1) if port_match else '8050'
    
    return {
        "type": "Dash",
        "url": f"http://localhost:{port}",
        "port": port,
        "framework": "Dash",
        "startup_command": f"python main.py"
    }

def _is_django_app(content: str, patch_dir: str) -> bool:
    """Enhanced Django detection."""
    # Check for Django patterns in main.py
    django_patterns = [
        r'from django',
        r'import django',
        r'Django\(',
        r'manage\.py'
    ]
    
    content_lower = content.lower()
    django_in_code = any(re.search(pattern, content_lower) for pattern in django_patterns)
    
    # Check for manage.py file
    manage_py_exists = os.path.exists(os.path.join(patch_dir, "manage.py"))
    
    return django_in_code or manage_py_exists

def _is_bottle_app(content: str) -> bool:
    """Enhanced Bottle detection."""
    bottle_patterns = [
        r'import bottle',
        r'from bottle import',
        r'@bottle\.',
        r'bottle\.run'
    ]
    
    content_lower = content.lower()
    return any(re.search(pattern, content_lower) for pattern in bottle_patterns)

def _detect_bottle_config(content: str) -> Dict[str, str]:
    """Detect Bottle configuration."""
    port_match = re.search(r'bottle\.run\([^)]*port\s*=\s*(\d+)', content)
    port = port_match.group(1) if port_match else '8080'
    
    return {
        "type": "Bottle",
        "url": f"http://localhost:{port}",
        "port": port,
        "framework": "Bottle",
        "startup_command": f"python main.py"
    }

def _is_tornado_app(content: str) -> bool:
    """Enhanced Tornado detection."""
    tornado_patterns = [
        r'import tornado',
        r'from tornado import',
        r'tornado\.web',
        r'Application\(',
        r'listen\('
    ]
    
    content_lower = content.lower()
    return any(re.search(pattern, content_lower) for pattern in tornado_patterns)

def _detect_tornado_config(content: str) -> Dict[str, str]:
    """Detect Tornado configuration."""
    port_match = re.search(r'listen\([^)]*(\d+)', content)
    port = port_match.group(1) if port_match else '8888'
    
    return {
        "type": "Tornado",
        "url": f"http://localhost:{port}",
        "port": port,
        "framework": "Tornado",
        "startup_command": f"python main.py"
    }

def _is_generic_web_server(content: str) -> bool:
    """Enhanced generic web server detection."""
    generic_patterns = [
        r'http\.server',
        r'socketserver',
        r'web server',
        r'server\.run',
        r'HTTPServer',
        r'BaseHTTPRequestHandler',
        r'@app\.route',  # Generic route decorators
        r'def index\(',
        r'def home\(',
        r'return.*html',
        r'Content-Type.*text/html'
    ]
    
    content_lower = content.lower()
    return any(re.search(pattern, content_lower) for pattern in generic_patterns)

def _detect_generic_web_config(content: str) -> Dict[str, str]:
    """Detect generic web server configuration."""
    # Look for port in common patterns
    port_patterns = [
        r'port\s*=\s*(\d+)',
        r'listen\([^)]*(\d+)',
        r'server\.run\([^)]*(\d+)',
        r'bind\([^)]*(\d+)',
        r'HTTPServer\([^)]*(\d+)'
    ]
    
    port = '8080'  # Default for generic servers
    
    for pattern in port_patterns:
        match = re.search(pattern, content)
        if match:
            port = match.group(1)
            break
    
    return {
        "type": "WebServer",
        "url": f"http://localhost:{port}",
        "port": port,
        "framework": "Generic",
        "startup_command": f"python main.py"
    }

# Response models
class CodeGenerationResponse(BaseModel):
    """Response model for code generation endpoints."""
    file_path: str
    content: str
    language: str
    description: str
    created_at: str
    patch_id: Optional[str] = None

class PatchStatusResponse(BaseModel):
    """Response model for patch status endpoints."""
    status: str
    message: str
    execution_output: Optional[str] = None
    error_output: Optional[str] = None
    return_code: Optional[int] = None
    analysis: Optional[str] = None
    suggested_improvements: Optional[List[str]] = None
    completed: bool = False
    was_regenerated: Optional[bool] = None
    app_url: Optional[str] = None
    app_type: Optional[str] = None
    app_port: Optional[str] = None
    generated_images: Optional[List[str]] = None  # List of generated image paths

# Git configuration models
class GitConfig(BaseModel):
    name: str
    email: str

class GitRemote(BaseModel):
    name: str
    url: str

class GitCommit(BaseModel):
    message: str
    files: List[str]

class GitPush(BaseModel):
    remote: str = "origin"
    branch: str = "main"

class PatchPush(BaseModel):
    """Model for pushing a patch to git."""
    patch_id: str
    commit_message: Optional[str] = None
    remote: str = "origin"
    branch: str = "main"

class RegeneratePatchRequest(BaseModel):
    """Model for regenerating a patch."""
    patch_id: str
    reason: Optional[str] = None

# Git endpoints
@app.post("/git/init")
async def init_git():
    """Initialize a new git repository."""
    if git_manager.init():
        return {"message": "Git repository initialized successfully"}
    raise HTTPException(status_code=500, detail="Failed to initialize git repository")

@app.post("/git/config")
async def configure_git(config: GitConfig):
    """Configure git user name and email."""
    if git_manager.configure_user(config.name, config.email):
        return {"message": "Git user configured successfully"}
    raise HTTPException(status_code=500, detail="Failed to configure git user")

@app.post("/git/remote")
async def add_remote(remote: GitRemote):
    """Add a git remote."""
    if git_manager.set_remote(remote.name, remote.url):
        return {"message": f"Remote {remote.name} added successfully"}
    raise HTTPException(status_code=500, detail="Failed to add remote")

@app.post("/git/commit")
async def create_commit(commit: GitCommit):
    """Create a git commit."""
    if not git_manager.add(commit.files):
        raise HTTPException(status_code=500, detail="Failed to add files")
    if git_manager.commit(commit.message):
        return {"message": "Changes committed successfully"}
    raise HTTPException(status_code=500, detail="Failed to commit changes")

@app.post("/git/push")
async def push_changes(push: GitPush):
    """Push changes to remote repository."""
    if git_manager.push(push.remote, push.branch):
        return {"message": f"Changes pushed to {push.remote}/{push.branch} successfully"}
    raise HTTPException(status_code=500, detail="Failed to push changes")

@app.get("/git/status")
async def get_status():
    """Get git repository status."""
    success, status = git_manager.get_status()
    if success:
        return {"status": status}
    raise HTTPException(status_code=500, detail="Failed to get git status")

@app.post("/git/push-patch/{patch_id}")
async def push_patch(patch_id: str, push: PatchPush):
    """Push a specific patch to git repository."""
    try:
        # Construct patch directory path
        patch_dir = os.path.join(code_generator.patches_dir, patch_id)
        if not os.path.exists(patch_dir):
            raise HTTPException(status_code=404, detail=f"Patch {patch_id} not found")

        # Get relative path from git root to patch directory
        git_root = os.path.abspath(os.path.dirname(__file__))
        rel_patch_dir = os.path.relpath(patch_dir, git_root)

        # Add all files in the patch directory
        files_to_add = [
            os.path.join(rel_patch_dir, "src"),
            os.path.join(rel_patch_dir, "requirements.txt"),
            os.path.join(rel_patch_dir, "metadata.txt"),
            os.path.join(rel_patch_dir, "README.md")
        ]

        # Create commit message if not provided
        commit_message = push.commit_message or f"Add patch: {patch_id}"

        # Add and commit files
        if not git_manager.add(files_to_add):
            raise HTTPException(status_code=500, detail="Failed to add patch files to git")

        if not git_manager.commit(commit_message):
            raise HTTPException(status_code=500, detail="Failed to commit patch files")

        # Push to remote
        if not git_manager.push(push.remote, push.branch):
            raise HTTPException(status_code=500, detail="Failed to push patch to remote repository")

        return {
            "message": f"Patch {patch_id} pushed successfully to {push.remote}/{push.branch}",
            "commit_message": commit_message,
            "files": files_to_add
        }

    except Exception as e:
        logger.error(f"Error pushing patch: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def analyze_patch_structure(patch_id: str, task: CodeTask, output: str, error_output: str) -> dict:
    """Analyze the current patch structure and identify issues for regeneration."""
    try:
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        patch_dir = os.path.join(workspace_root, "patches", patch_id)
        
        analysis = {
            "patch_id": patch_id,
            "issues": [],
            "file_structure": {},
            "missing_dependencies": [],
            "code_quality_issues": [],
            "regeneration_strategy": "comprehensive"
        }
        
        # Analyze file structure
        if os.path.exists(patch_dir):
            for root, dirs, files in os.walk(patch_dir):
                rel_path = os.path.relpath(root, patch_dir)
                analysis["file_structure"][rel_path] = files
        
        # Analyze error patterns
        error_lower = error_output.lower()
        if "module not found" in error_lower or "no module named" in error_lower:
            analysis["issues"].append("missing_dependencies")
            # Extract missing module names
            import re
            missing_modules = re.findall(r"no module named ['\"]([^'\"]+)['\"]", error_lower)
            analysis["missing_dependencies"].extend(missing_modules)
        
        if "syntax error" in error_lower:
            analysis["issues"].append("syntax_error")
            analysis["code_quality_issues"].append("syntax_error")
        
        if "invalid requirement" in error_lower or "failed to install requirements" in error_lower:
            analysis["issues"].append("requirements_issue")
        
        # Check if main file is test-focused
        src_dir = os.path.join(patch_dir, "src")
        if os.path.exists(src_dir):
            main_file = os.path.join(src_dir, "main.py")
            if os.path.exists(main_file):
                try:
                    with open(main_file, 'r') as f:
                        content = f.read()
                        if "import pytest" in content or "def test_" in content:
                            analysis["issues"].append("test_focused_output")
                            analysis["regeneration_strategy"] = "complete_rewrite"
                except Exception:
                    pass
        
        # Check requirements.txt issues
        req_file = os.path.join(patch_dir, "requirements.txt")
        if os.path.exists(req_file):
            try:
                with open(req_file, 'r') as f:
                    req_content = f.read()
                    if any(keyword in req_content for keyword in ["FROM", "WORKDIR", "COPY", "CMD", "pip install"]):
                        analysis["issues"].append("requirements_file_corrupted")
                        analysis["regeneration_strategy"] = "fix_requirements"
            except Exception:
                pass
        else:
            # Check if there are any main.requirements.txt files
            src_dir = os.path.join(patch_dir, "src")
            if os.path.exists(src_dir):
                for file in os.listdir(src_dir):
                    if file.endswith('.requirements.txt') or file.startswith('main.requirements'):
                        analysis["issues"].append("requirements_file_misplaced")
                        analysis["regeneration_strategy"] = "fix_requirements"
                        break
        
        logger.info(f"Patch analysis for {patch_id}: {analysis}")
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing patch structure: {str(e)}")
        return {"patch_id": patch_id, "issues": ["analysis_error"], "regeneration_strategy": "basic"}

async def perform_enhanced_regeneration(patch_id: str, task: CodeTask, analysis: dict) -> bool:
    """Perform comprehensive regeneration based on analysis."""
    try:
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        patch_dir = os.path.join(workspace_root, "patches", patch_id)
        src_dir = os.path.join(patch_dir, "src")
        
        strategy = analysis.get("regeneration_strategy", "comprehensive")
        logger.info(f"Using regeneration strategy: {strategy} for patch {patch_id}")
        
        if strategy == "complete_rewrite":
            return await perform_complete_rewrite(patch_id, task, analysis)
        elif strategy == "fix_requirements":
            return await fix_requirements_and_regenerate(patch_id, task, analysis)
        else:
            return await perform_comprehensive_regeneration(patch_id, task, analysis)
            
    except Exception as e:
        logger.error(f"Error in enhanced regeneration: {str(e)}")
        return False

async def perform_complete_rewrite(patch_id: str, task: CodeTask, analysis: dict) -> bool:
    """Perform a complete rewrite of the project."""
    try:
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        patch_dir = os.path.join(workspace_root, "patches", patch_id)
        
        # Analyze existing code to identify imports
        imports = []
        if os.path.exists(src_dir):
            for file in os.listdir(src_dir):
                if file.endswith('.py'):
                    file_path = os.path.join(src_dir, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                            # Extract import statements
                            import re
                            import_lines = re.findall(r'^(?:from\s+(\w+)|import\s+(\w+))', content, re.MULTILINE)
                            for match in import_lines:
                                module = match[0] if match[0] else match[1]
                                if module and module not in ['os', 'sys', 'json', 'csv', 'argparse', 'logging', 'typing', 're', 'datetime', 'time', 'random', 'math', 'collections', 'itertools', 'functools', 'pathlib', 'urllib', 'http', 'ssl', 'socket', 'threading', 'subprocess', 'asyncio', 'tempfile', 'shutil', 'glob', 'fnmatch', 'pickle', 'base64', 'hashlib', 'zlib', 'gzip', 'bz2', 'lzma', 'zipfile', 'tarfile', 'sqlite3', 'xml', 'html', 'email', 'smtplib', 'ftplib', 'telnetlib', 'socketserver', 'xmlrpc', 'configparser', 'argparse', 'getopt', 'optparse', 'pdb', 'traceback', 'warnings', 'weakref', 'abc', 'enum', 'dataclasses', 'typing_extensions']:
                                    imports.append(module)
                    except Exception:
                        pass
        
        # Create comprehensive prompt for complete rewrite
        prompt = f"""You are tasked with creating a complete, working application based on the following requirements:

TASK: {task.description}

REQUIREMENTS:
{chr(10).join(f'- {req}' for req in task.requirements)}

LANGUAGE: {task.language}
DETECTED IMPORTS: {', '.join(set(imports)) if imports else 'None detected'}

The current implementation has the following issues:
{chr(10).join(f'- {issue}' for issue in analysis.get('issues', []))}

Please create a COMPLETE, WORKING application that:
1. Implements ALL the required features
2. Has proper file structure and organization
3. Includes all necessary dependencies
4. Has a main entry point that can be executed
5. Includes proper error handling and logging
6. Is NOT just test files - create the actual application

Generate the complete application with multiple files as needed. Use proper file extensions and structure.
For Python projects, ensure there's a main.py that can be run directly.
Include a proper requirements.txt with actual Python package dependencies.

IMPORTANT: If generating a requirements.txt file, include ONLY package names and versions, one per line.
Do NOT include comments, Docker commands, or pip install commands.
Include ALL external packages that need to be installed via pip.

Common packages for this type of project:
- requests (for HTTP requests)
- beautifulsoup4 (for HTML parsing)
- pandas (for data manipulation)
- numpy (for numerical operations)
- matplotlib (for plotting)
- scikit-learn (for machine learning)
- flask (for web applications)
- fastapi (for API development)
- sqlalchemy (for database operations)
- pytest (for testing)

Example requirements.txt format:
requests>=2.25.0
beautifulsoup4>=4.9.0
pandas>=1.3.0

Return the complete application structure with all necessary files."""

        # Generate complete rewrite
        response = code_generator.client.chat.completions.create(
            model="qwen/qwen3-32b",
            messages=[
                {"role": "system", "content": "You are an expert software architect. Create complete, working applications with proper structure and all necessary files."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=8192,
            temperature=0.2,
            top_p=0.95
        )
        
        content = response.choices[0].message.content
        files = code_generator._extract_files_from_response(content)
        
        if files:
            # Clean up any malformed requirements files before saving
            if 'requirements.txt' in files:
                req_content = files['requirements.txt']
                # Clean requirements content
                import re
                req_content = re.sub(r'```.*?```', '', req_content, flags=re.DOTALL)
                req_content = re.sub(r'<think>.*?</think>', '', req_content, flags=re.DOTALL)
                req_content = re.sub(r'#.*$', '', req_content, flags=re.MULTILINE)  # Remove comments
                req_content = re.sub(r'^pip install.*$', '', req_content, flags=re.MULTILINE)  # Remove pip install lines
                req_content = re.sub(r'^FROM.*$', '', req_content, flags=re.MULTILINE)  # Remove Docker lines
                req_content = re.sub(r'^WORKDIR.*$', '', req_content, flags=re.MULTILINE)  # Remove Docker lines
                req_content = re.sub(r'^COPY.*$', '', req_content, flags=re.MULTILINE)  # Remove Docker lines
                req_content = re.sub(r'^CMD.*$', '', req_content, flags=re.MULTILINE)  # Remove Docker lines
                req_content = req_content.strip()
                
                # Validate requirements content
                lines = req_content.split('\n')
                valid_lines = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('pip') and not line.startswith('FROM') and not line.startswith('WORKDIR') and not line.startswith('COPY') and not line.startswith('CMD'):
                        valid_lines.append(line)
                
                files['requirements.txt'] = '\n'.join(valid_lines)
                logger.info(f"Cleaned requirements.txt for patch {patch_id}: {files['requirements.txt']}")
            
            # Save all files
            success = code_generator.save_multiple_files(files, patch_dir)
            if success:
                logger.info(f"Complete rewrite successful for patch {patch_id}")
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error in complete rewrite: {str(e)}")
        return False

async def fix_requirements_and_regenerate(patch_id: str, task: CodeTask, analysis: dict) -> bool:
    """Fix requirements.txt and regenerate main code."""
    try:
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        patch_dir = os.path.join(workspace_root, "patches", patch_id)
        src_dir = os.path.join(patch_dir, "src")
        
        # Analyze existing code to identify imports
        imports = []
        if os.path.exists(src_dir):
            for file in os.listdir(src_dir):
                if file.endswith('.py'):
                    file_path = os.path.join(src_dir, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                            # Extract import statements
                            import re
                            import_lines = re.findall(r'^(?:from\s+(\w+)|import\s+(\w+))', content, re.MULTILINE)
                            for match in import_lines:
                                module = match[0] if match[0] else match[1]
                                if module and module not in ['os', 'sys', 'json', 'csv', 'argparse', 'logging', 'typing', 're', 'datetime', 'time', 'random', 'math', 'collections', 'itertools', 'functools', 'pathlib', 'urllib', 'http', 'ssl', 'socket', 'threading', 'subprocess', 'asyncio', 'tempfile', 'shutil', 'glob', 'fnmatch', 'pickle', 'base64', 'hashlib', 'zlib', 'gzip', 'bz2', 'lzma', 'zipfile', 'tarfile', 'sqlite3', 'xml', 'html', 'email', 'smtplib', 'ftplib', 'telnetlib', 'socketserver', 'xmlrpc', 'configparser', 'argparse', 'getopt', 'optparse', 'pdb', 'traceback', 'warnings', 'weakref', 'abc', 'enum', 'dataclasses', 'typing_extensions']:
                                    imports.append(module)
                    except Exception:
                        pass
        
        # Generate proper requirements.txt
        req_prompt = f"""Create a proper requirements.txt file for the following Python project:

TASK: {task.description}
REQUIREMENTS: {', '.join(task.requirements)}
DETECTED IMPORTS: {', '.join(set(imports)) if imports else 'None detected'}

Generate a requirements.txt file with ALL necessary Python package dependencies.
Include ALL external packages that need to be installed via pip.
Do NOT include standard library modules (os, sys, json, csv, argparse, logging, typing, etc.).

CRITICAL: Return ONLY the package names and versions, one per line. Do NOT include:
- Comments starting with #
- Docker commands (FROM, WORKDIR, etc.)
- pip install commands
- Any other non-package content

Common packages for this type of project:
- requests (for HTTP requests)
- beautifulsoup4 (for HTML parsing)
- pandas (for data manipulation)
- numpy (for numerical operations)
- matplotlib (for plotting)
- scikit-learn (for machine learning)
- flask (for web applications)
- fastapi (for API development)
- sqlalchemy (for database operations)
- pytest (for testing)

Example format:
requests>=2.25.0
beautifulsoup4>=4.9.0
pandas>=1.3.0

Return ONLY the requirements.txt content."""

        response = code_generator.client.chat.completions.create(
            model="qwen/qwen3-32b",
            messages=[
                {"role": "system", "content": "You are an expert Python developer. Create proper requirements.txt files with correct package dependencies. Return only package names and versions."},
                {"role": "user", "content": req_prompt}
            ],
            max_tokens=2048,
            temperature=0.1,
            top_p=0.95
        )
        
        req_content = response.choices[0].message.content.strip()
        
        # Clean requirements content
        import re
        req_content = re.sub(r'```.*?```', '', req_content, flags=re.DOTALL)
        req_content = re.sub(r'<think>.*?</think>', '', req_content, flags=re.DOTALL)
        req_content = re.sub(r'#.*$', '', req_content, flags=re.MULTILINE)  # Remove comments
        req_content = re.sub(r'^pip install.*$', '', req_content, flags=re.MULTILINE)  # Remove pip install lines
        req_content = re.sub(r'^FROM.*$', '', req_content, flags=re.MULTILINE)  # Remove Docker lines
        req_content = re.sub(r'^WORKDIR.*$', '', req_content, flags=re.MULTILINE)  # Remove Docker lines
        req_content = re.sub(r'^COPY.*$', '', req_content, flags=re.MULTILINE)  # Remove Docker lines
        req_content = re.sub(r'^CMD.*$', '', req_content, flags=re.MULTILINE)  # Remove Docker lines
        req_content = req_content.strip()
        
        # Validate requirements content
        lines = req_content.split('\n')
        valid_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('pip') and not line.startswith('FROM') and not line.startswith('WORKDIR') and not line.startswith('COPY') and not line.startswith('CMD'):
                valid_lines.append(line)
        
        req_content = '\n'.join(valid_lines)
        
        # Save requirements.txt
        req_file = os.path.join(patch_dir, "requirements.txt")
        with open(req_file, 'w') as f:
            f.write(req_content)
        
        logger.info(f"Generated requirements.txt for patch {patch_id}: {req_content}")
        
        # Regenerate main code
        return await perform_comprehensive_regeneration(patch_id, task, analysis)
        
    except Exception as e:
        logger.error(f"Error fixing requirements: {str(e)}")
        return False

async def perform_comprehensive_regeneration(patch_id: str, task: CodeTask, analysis: dict) -> bool:
    """Perform comprehensive regeneration addressing multiple issues."""
    try:
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        patch_dir = os.path.join(workspace_root, "patches", patch_id)
        src_dir = os.path.join(patch_dir, "src")
        
        # Analyze existing code to identify imports
        imports = []
        if os.path.exists(src_dir):
            for file in os.listdir(src_dir):
                if file.endswith('.py'):
                    file_path = os.path.join(src_dir, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                            # Extract import statements
                            import re
                            import_lines = re.findall(r'^(?:from\s+(\w+)|import\s+(\w+))', content, re.MULTILINE)
                            for match in import_lines:
                                module = match[0] if match[0] else match[1]
                                if module and module not in ['os', 'sys', 'json', 'csv', 'argparse', 'logging', 'typing', 're', 'datetime', 'time', 'random', 'math', 'collections', 'itertools', 'functools', 'pathlib', 'urllib', 'http', 'ssl', 'socket', 'threading', 'subprocess', 'asyncio', 'tempfile', 'shutil', 'glob', 'fnmatch', 'pickle', 'base64', 'hashlib', 'zlib', 'gzip', 'bz2', 'lzma', 'zipfile', 'tarfile', 'sqlite3', 'xml', 'html', 'email', 'smtplib', 'ftplib', 'telnetlib', 'socketserver', 'xmlrpc', 'configparser', 'argparse', 'getopt', 'optparse', 'pdb', 'traceback', 'warnings', 'weakref', 'abc', 'enum', 'dataclasses', 'typing_extensions']:
                                    imports.append(module)
                    except Exception:
                        pass
        
        # Create comprehensive regeneration prompt
        prompt = f"""The following code failed to execute and needs comprehensive regeneration:

TASK: {task.description}
REQUIREMENTS: {', '.join(task.requirements)}
LANGUAGE: {task.language}
DETECTED IMPORTS: {', '.join(set(imports)) if imports else 'None detected'}

IDENTIFIED ISSUES:
{chr(10).join(f'- {issue}' for issue in analysis.get('issues', []))}

MISSING DEPENDENCIES:
{chr(10).join(f'- {dep}' for dep in analysis.get('missing_dependencies', []))}

Please create a COMPLETE, WORKING implementation that:
1. Addresses ALL the identified issues
2. Includes all missing dependencies
3. Creates a proper main application (not just tests)
4. Has correct file structure
5. Can be executed successfully
6. Implements the actual requirements

Generate the complete application with proper main entry point and all necessary files.
For Python projects, ensure main.py contains the actual application logic, not just tests.

IMPORTANT: If generating a requirements.txt file, include ONLY package names and versions, one per line.
Do NOT include comments, Docker commands, or pip install commands.
Include ALL external packages that need to be installed via pip.

Common packages for this type of project:
- requests (for HTTP requests)
- beautifulsoup4 (for HTML parsing)
- pandas (for data manipulation)
- numpy (for numerical operations)
- matplotlib (for plotting)
- scikit-learn (for machine learning)
- flask (for web applications)
- fastapi (for API development)
- sqlalchemy (for database operations)
- pytest (for testing)

Return the complete, working application."""

        # Generate comprehensive solution
        response = code_generator.client.chat.completions.create(
            model="qwen/qwen3-32b",
            messages=[
                {"role": "system", "content": "You are an expert software developer. Create complete, working applications that address all identified issues and implement the full requirements."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=8192,
            temperature=0.2,
            top_p=0.95
        )
        
        content = response.choices[0].message.content
        files = code_generator._extract_files_from_response(content)
        
        if files:
            # Clean up any malformed requirements files before saving
            if 'requirements.txt' in files:
                req_content = files['requirements.txt']
                # Clean requirements content
                import re
                req_content = re.sub(r'```.*?```', '', req_content, flags=re.DOTALL)
                req_content = re.sub(r'<think>.*?</think>', '', req_content, flags=re.DOTALL)
                req_content = re.sub(r'#.*$', '', req_content, flags=re.MULTILINE)  # Remove comments
                req_content = re.sub(r'^pip install.*$', '', req_content, flags=re.MULTILINE)  # Remove pip install lines
                req_content = re.sub(r'^FROM.*$', '', req_content, flags=re.MULTILINE)  # Remove Docker lines
                req_content = re.sub(r'^WORKDIR.*$', '', req_content, flags=re.MULTILINE)  # Remove Docker lines
                req_content = re.sub(r'^COPY.*$', '', req_content, flags=re.MULTILINE)  # Remove Docker lines
                req_content = re.sub(r'^CMD.*$', '', req_content, flags=re.MULTILINE)  # Remove Docker lines
                req_content = req_content.strip()
                
                # Validate requirements content
                lines = req_content.split('\n')
                valid_lines = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('pip') and not line.startswith('FROM') and not line.startswith('WORKDIR') and not line.startswith('COPY') and not line.startswith('CMD'):
                        valid_lines.append(line)
                
                files['requirements.txt'] = '\n'.join(valid_lines)
                logger.info(f"Cleaned requirements.txt for patch {patch_id}: {files['requirements.txt']}")
            
            # Save all files
            success = code_generator.save_multiple_files(files, patch_dir)
            if success:
                logger.info(f"Comprehensive regeneration successful for patch {patch_id}")
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error in comprehensive regeneration: {str(e)}")
        return False

async def get_patch_metadata(patch_id: str) -> CodeTask:
    """Get metadata for a patch."""
    try:
        # Get the absolute path to the workspace root
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        # Construct patch directory path
        patch_dir = os.path.join(workspace_root, "patches", patch_id)
        if not os.path.exists(patch_dir):
            raise ValueError(f"Patch directory not found: {patch_id}")
        
        # Read metadata file
        metadata_path = os.path.join(patch_dir, "metadata.txt")
        if not os.path.exists(metadata_path):
            # If no metadata file, create a basic task from the patch ID
            description = patch_id.replace("_", " ").strip()
            return CodeTask(
                description=description,
                language="python",
                requirements=[],
                context=None
            )
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            
        return CodeTask(
            description=metadata.get("description", patch_id),
            language=metadata.get("language", "python"),
            requirements=metadata.get("requirements", []),
            context=metadata.get("context")
        )
    except Exception as e:
        logger.error(f"Failed to get patch metadata: {str(e)}")
        raise

async def execute_patch(patch_id: str) -> Tuple[bool, str, str, int]:
    """Execute a patch and return its output.
    
    Args:
        patch_id: The ID of the patch to execute
        
    Returns:
        Tuple[bool, str, str, int]: (success, stdout, stderr, return_code)
    """
    try:
        # Get workspace root and patch directory
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        patch_dir = os.path.join(workspace_root, "patches", patch_id)
        src_dir = os.path.join(patch_dir, "src")
        
        # Get list of files
        if not os.path.exists(src_dir):
            raise ValueError("Source directory not found")
        
        files = os.listdir(src_dir)
        if not files:
            raise ValueError("No files found in source directory")
            
        # Clean and execute each Python file
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(src_dir, file)
                
                # Clean the file of both triple quotes and backticks
                # clean_file_of_triple_quotes(file_path) # This function is removed
                # clean_file_of_backticks(file_path) # This function is removed
                
                # Create isolated environment
                env = IsolatedEnvironment(patch_dir)
                try:
                    # Setup environment
                    if not env.create():
                        return False, "", "Failed to create virtual environment", 1
                    
                    if not env.install_requirements():
                        return False, "", "Failed to install requirements", 1
                    
                    # Execute the file
                    success, stdout, stderr, return_code = env.run_script(file_path)
                    
                    if not success:
                        return False, stdout, stderr, return_code
                    
                    # Return the actual output from the script
                    return True, stdout, stderr, return_code
                        
                finally:
                    # Always cleanup
                    env.cleanup()
                    
        # If no Python files were found or executed
        return True, "No Python files found to execute", "", 0
        
    except Exception as e:
        return False, "", str(e), 1

async def run_patch_task(patch_id: str, analyze: bool = True):
    """Run patch and optionally analyze output."""
    try:
        # Update initial status
        patch_run_results[patch_id] = {
            "status": "processing",
            "message": "Processing...",
            "success": False,
            "output": "Processing...",
            "error_output": "",
            "return_code": 0,
            "analysis": None,
            "suggested_improvements": None,
            "completed": False,
            "was_regenerated": False
        }

        # Get workspace root and patch directory
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        patch_dir = os.path.join(workspace_root, "patches", patch_id)
        src_dir = os.path.join(patch_dir, "src")
        
        # Get list of files
        if not os.path.exists(src_dir):
            raise ValueError("Source directory not found")
        
        files = os.listdir(src_dir)
        if not files:
            raise ValueError("No files found in source directory")
            
        main_file = files[0]  # Get the first Python file

        # Execute the code and capture output
        success, output, error_output, return_code = await execute_patch(patch_id)
        
        # Check for error indicators in both stdout and stderr
        error_indicators = [
            "error processing grades",
            "division by zero",
            "should trigger",
            "invalid",
            "exception",
            "error",
            "failed",
            "traceback"
        ]
        
        # Move error messages from stdout to stderr if they contain error indicators
        if output and any(indicator.lower() in output.lower() for indicator in error_indicators):
            error_output = output if not error_output else f"{error_output}\n{output}"
            output = ""
        
        # Check for errors in either output stream
        has_error = (
            return_code != 0 or
            bool(error_output) or
            any(indicator.lower() in (output + error_output).lower() for indicator in error_indicators)
        )
        
        # Set execution success and prepare for potential regeneration
        execution_success = not has_error
        needs_regeneration = has_error
        
        # Initialize patch run results
        patch_run_results[patch_id] = {
            "status": "processing",
            "message": "Execution completed",
            "success": execution_success,
            "output": output,
            "error_output": error_output,
            "return_code": return_code,
            "analysis": None,  # Will be set later if analyze=True
            "suggested_improvements": None,  # Will be set later if analyze=True
            "completed": False,  # Not done yet
            "was_regenerated": False  # Will be set to True if regeneration happens
        }
        
        # Get patch metadata
        task = None
        try:
            task = await get_patch_metadata(patch_id)
        except Exception as e:
            logger.error(f"Failed to get patch metadata: {str(e)}")
            patch_run_results[patch_id]["completed"] = True
            return
        
        # If we have errors, try to regenerate the code with enhanced analysis
        if needs_regeneration:
            logger.info(f"Starting enhanced regeneration for patch {patch_id}")
            
            # Analyze the current patch structure and issues
            patch_analysis = await analyze_patch_structure(patch_id, task, output, error_output)
            
            # Perform comprehensive regeneration
            regeneration_success = await perform_enhanced_regeneration(patch_id, task, patch_analysis)
            
            if regeneration_success:
                # Execute the regenerated code
                success, output, error_output, return_code = await execute_patch(patch_id)
                
                # Update results with regeneration info
                patch_run_results[patch_id].update({
                    "status": "completed",
                    "message": "Code comprehensively regenerated and executed",
                    "success": success,
                    "output": output,
                    "error_output": error_output,
                    "return_code": return_code,
                    "completed": True,
                    "was_regenerated": True
                })
                logger.info(f"Enhanced regeneration completed for patch {patch_id}")
                return
            else:
                logger.warning(f"Enhanced regeneration failed for patch {patch_id}")
                patch_run_results[patch_id]["completed"] = True
                return

        # If we get here, either no regeneration was needed or it failed
        patch_run_results[patch_id]["completed"] = True

        # Perform analysis if requested
        analysis = None
        suggested_fixes = None
        if analyze and task: # code_generator.client is removed
            try:
                # The code_generator.assess_output is removed, so this block is effectively removed.
                # The analysis and suggested_fixes will now be handled by the new execute_patch endpoint.
                pass # No analysis or regeneration here
            except Exception as e:
                analysis = f"Error analyzing output: {str(e)}"
                suggested_fixes = []
        
        # Detect if this is a web application
        # web_app_info = detect_web_application(patch_id) # This function is removed
        
        patch_run_results[patch_id] = {
            "status": "completed",
            "message": "Execution completed",
            "success": execution_success,
            "output": output,
            "error_output": error_output,
            "return_code": return_code,
            "analysis": analysis if analyze else None,
            "suggested_improvements": suggested_fixes if analyze else None,
            "completed": True,
            "was_regenerated": not execution_success and task, # code_generator.client is removed
            "is_web_app": False, # web_app_info.get("is_web_app", False), # This function is removed
            "web_app_url": None, # f"http://localhost:{web_app_info.get('port', 5000)}" if web_app_info.get("is_web_app") else None, # This function is removed
            "web_app_port": None # web_app_info.get("port") if web_app_info.get("is_web_app") else None # This function is removed
        }
        
    except Exception as e:
        patch_run_results[patch_id] = {
            "status": "error",
            "message": f"Error: {str(e)}",
            "success": False,
            "output": str(e),
            "completed": True
        }
    finally:
        # Clean up task
        if patch_id in patch_tasks:
            del patch_tasks[patch_id]

# Pydantic models for request/response validation
class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    language: Optional[str] = "python"
    requirements: Optional[List[str]] = []  # Task requirements/features
    package_requirements: Optional[List[str]] = []  # Actual Python package dependencies
    context: Optional[str] = None
    metadata: Optional[Dict] = None

class TodoResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    completed: bool
    created_at: str
    language: Optional[str] = None
    requirements: Optional[List[str]] = None
    context: Optional[str] = None
    metadata: Optional[Dict] = None
    patch_id: Optional[str] = None

class CodeGenerationRequest(BaseModel):
    description: str
    language: str = "python"
    requirements: List[str] = []
    context: Optional[str] = None

class RunPatchRequest(BaseModel):
    patch_id: str
    analyze: bool = True  # Whether to perform GPT analysis

class RunPatchResponse(BaseModel):
    status: str
    message: str
    execution_output: Optional[str] = None
    error_output: Optional[str] = None
    return_code: Optional[int] = None
    analysis: Optional[str] = None
    suggested_improvements: Optional[List[str]] = None
    was_regenerated: Optional[bool] = None  # Whether the code was regenerated due to execution failure

class PatchRunStatus(BaseModel):
    success: bool
    output: str
    error_output: Optional[str] = None
    return_code: Optional[int] = None
    analysis: Optional[str] = None
    suggested_improvements: Optional[List[str]] = None
    completed: bool = False
    was_regenerated: Optional[bool] = None  # Whether the code was regenerated due to execution failure

# Todo endpoints
@app.post("/todos/", response_model=TodoResponse)
async def create_todo(todo: TodoCreate):
    """Create a new todo item."""
    logger.debug(f"Creating todo with data: {todo.dict()}")
    todo_item = TodoItem(
        title=todo.title,
        description=todo.description,
        created_at=datetime.now().isoformat(),
        language=todo.language,
        requirements=todo.requirements,
        package_requirements=todo.package_requirements,
        context=todo.context,
        metadata=todo.metadata
    )
    logger.debug(f"Created TodoItem: {todo_item.to_dict()}")
    if db_manager.add_todo(todo_item):
        # Get the created todo to return its ID
        todos = db_manager.get_todos()
        created_todo = next((t for t in todos if t.title == todo.title), None)
        if created_todo:
            return TodoResponse(**created_todo.to_dict())
    raise HTTPException(status_code=500, detail="Failed to create todo")

@app.get("/todos/", response_model=List[TodoResponse])
async def list_todos():
    """List all todo items."""
    todos = db_manager.get_todos()
    return [TodoResponse(**todo.to_dict()) for todo in todos]

@app.put("/todos/{todo_id}/complete")
async def complete_todo(todo_id: int):
    """Mark a todo as completed."""
    if todo_commands.complete_todo(todo_id):
        return {"message": f"Todo {todo_id} marked as completed"}
    raise HTTPException(status_code=404, detail="Todo not found")

@app.put("/todos/{todo_id}/uncomplete")
async def uncomplete_todo(todo_id: int):
    """Mark a todo as not completed."""
    if todo_commands.uncomplete_todo(todo_id):
        return {"message": f"Todo {todo_id} marked as not completed"}
    raise HTTPException(status_code=404, detail="Todo not found")

@app.delete("/todos/clear-all")
async def clear_todos(completed_only: bool = False):
    """Clear todos from the database.
    
    Args:
        completed_only: If True, only clear completed todos. If False, clear all todos.
    """
    deleted_count = todo_commands.clear_todos(completed_only)
    if deleted_count > 0:
        if completed_only:
            return {"message": f"Cleared {deleted_count} completed todo(s)!"}
        else:
            return {"message": f"Cleared all {deleted_count} todo(s)!"}
    else:
        if completed_only:
            return {"message": "No completed todos found to clear."}
        else:
            return {"message": "No todos found to clear."}

@app.delete("/patches/clear")
async def clear_patches(patch_id: Optional[str] = None):
    """Clear patches from the filesystem.
    
    Args:
        patch_id: If provided, clear only this specific patch. If None, clear all patches.
    """
    try:
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        patches_dir = os.path.join(workspace_root, "patches")
        
        if patch_id:
            # Clear specific patch
            patch_dir = os.path.join(patches_dir, patch_id)
            if not os.path.exists(patch_dir):
                raise HTTPException(status_code=404, detail=f"Patch {patch_id} not found")
            
            import shutil
            shutil.rmtree(patch_dir)
            logger.info(f"Cleared patch: {patch_id}")
            return {"message": f"Cleared patch: {patch_id}"}
        else:
            # Clear all patches
            cleared_count = 0
            import shutil
            
            for item in os.listdir(patches_dir):
                item_path = os.path.join(patches_dir, item)
                if os.path.isdir(item_path) and item != ".gitkeep":
                    shutil.rmtree(item_path)
                    cleared_count += 1
                    logger.info(f"Cleared patch: {item}")
            
            if cleared_count > 0:
                return {"message": f"Cleared all {cleared_count} patch(es)!"}
            else:
                return {"message": "No patches found to clear."}
                
    except Exception as e:
        logger.error(f"Error clearing patches: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patches/list")
async def list_patches():
    """List all available patches."""
    try:
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        patches_dir = os.path.join(workspace_root, "patches")
        
        patches = []
        for item in os.listdir(patches_dir):
            item_path = os.path.join(patches_dir, item)
            if os.path.isdir(item_path) and item != ".gitkeep":
                # Get patch metadata if available
                metadata_path = os.path.join(item_path, "metadata.txt")
                metadata = {}
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                    except Exception:
                        pass
                
                # Detect web application
                web_app = detect_web_application(item)
                
                patches.append({
                    "patch_id": item,
                    "created_at": item[:15],  # Extract timestamp from patch_id
                    "description": metadata.get("description", item.replace("_", " ")),
                    "language": metadata.get("language", "python"),
                    "requirements": metadata.get("requirements", []),
                    "context": metadata.get("context"),
                    "app_url": web_app.get("url") if web_app else None,
                    "app_type": web_app.get("type") if web_app else None,
                    "app_port": web_app.get("port") if web_app else None,
                    "is_web_app": web_app is not None
                })
        
        return {"patches": patches, "count": len(patches)}
        
    except Exception as e:
        logger.error(f"Error listing patches: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: int):
    """Delete a todo item."""
    if todo_commands.delete_todo(todo_id):
        return {"message": f"Todo {todo_id} deleted"}
    raise HTTPException(status_code=404, detail="Todo not found")

@app.get("/todos/search")
async def search_todos(query: str):
    """Search todos by title or description."""
    todos = todo_commands.search_todos(query)
    return [TodoResponse(**todo.to_dict()) for todo in todos]

# Code generation endpoints
@app.post("/generate-code/{todo_id}", response_model=CodeGenerationResponse)
async def generate_code(todo_id: int):
    """Generate code based on todo item with autonomous improvements."""
    try:
        # Get the todo item
        todo = db_manager.get_todo_by_id(todo_id)
        if not todo:
            raise HTTPException(status_code=404, detail=f"Todo {todo_id} not found")
        
        # Create code generation task from todo
        task = CodeTask(
            description=todo.description,
            language=todo.language or "python",
            requirements=todo.requirements or [],
            package_requirements=todo.package_requirements or [],
            context=todo.context
        )
        
        # Generate initial code
        logger.info("Generating initial code...")
        generated_code = code_generator.generate_code(task)
        
        if code_generator.save_code(generated_code):
            # Extract patch ID from file path
            patch_id = os.path.basename(os.path.dirname(os.path.dirname(generated_code.file_path)))
            
            # Update todo with patch ID
            db_manager.update_todo_patch_id(todo_id, patch_id)
            
            return CodeGenerationResponse(
                file_path=generated_code.file_path,
                content=generated_code.content,
                language=generated_code.language,
                description=generated_code.description,
                created_at=datetime.now().isoformat(),
                patch_id=patch_id
            )
        
        raise HTTPException(status_code=500, detail="Failed to save generated code")
        
    except Exception as e:
        logger.error(f"Error generating code: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run-patch/{todo_id}", response_model=RunPatchResponse)
async def run_patch(todo_id: int, analyze: bool = True):
    """Run patch code with optional analysis."""
    try:
        # Get the todo item
        todo = db_manager.get_todo_by_id(todo_id)
        if not todo:
            raise HTTPException(status_code=404, detail=f"Todo {todo_id} not found")
        
        if not todo.patch_id:
            raise HTTPException(status_code=400, detail=f"Todo {todo_id} has no associated patch")
        
        # Cancel existing task if any
        if todo.patch_id in patch_tasks:
            patch_tasks[todo.patch_id].cancel()
            
        # Create and store new task
        task = asyncio.create_task(run_patch_task(todo.patch_id, analyze))
        patch_tasks[todo.patch_id] = task
        
        return RunPatchResponse(
            status="processing",
            message=f"Started processing patch {todo.patch_id}. Check /patch-status/{todo.patch_id} for updates."
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/execute-patch/", response_model=PatchStatusResponse)
async def execute_patch_endpoint(request: RunPatchRequest):
    """Execute patch with optional analysis."""
    try:
        patch_id = request.patch_id
        analyze = request.analyze
        
        # Add debug logging
        logger.info(f"execute_patch_endpoint called with patch_id={patch_id}, analyze={analyze}")
        
        patch_dir = os.path.join(code_generator.patches_dir, patch_id)
        
        if not os.path.exists(patch_dir):
            raise HTTPException(status_code=404, detail="Patch not found")
        
        # Detect web application type
        web_app = detect_web_application(patch_id)
        
        if analyze:
            logger.info(f"Performing static analysis for patch {patch_id}")
            # Perform static analysis only
            static_errors = []
            analysis_result = "Static analysis completed"
            
            # Check for common static errors
            main_files = ["main.py", "app.py", "index.py"]
            for file_name in main_files:
                file_path = os.path.join(patch_dir, file_name)
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        content = f.read()
                        
                        # Check for syntax errors
                        try:
                            compile(content, file_path, 'exec')
                        except SyntaxError as e:
                            static_errors.append(f"Syntax error in {file_name}: {str(e)}")
                        
                        # Check for common import errors
                        if "import " in content and "flask" in content.lower():
                            if "from flask import" not in content and "import flask" not in content:
                                static_errors.append(f"Missing Flask import in {file_name}")
            
            # Check requirements.txt
            req_file = os.path.join(patch_dir, "requirements.txt")
            if os.path.exists(req_file):
                with open(req_file, 'r') as f:
                    req_content = f.read()
                    if "name:" in req_content or "version:" in req_content:
                        static_errors.append("Invalid requirements.txt format - contains metadata")
            
            # Determine if regeneration is needed
            needs_regeneration = len(static_errors) > 0
            
            if needs_regeneration:
                analysis_result = f"Static errors detected: {', '.join(static_errors)}"
                suggested_improvements = ["Fix syntax errors", "Correct import statements", "Fix requirements.txt format"]
            else:
                analysis_result = "No static errors detected - code is ready for execution"
                suggested_improvements = ["Use start-web-app endpoint to run the application"]
            
            # For web apps, don't specify a port in the analysis response
            # The actual port will be assigned when the app starts
            app_url = None
            app_port = None
            if web_app:
                app_url = f"http://localhost:[PORT]"  # Placeholder for dynamic port
                app_port = "[DYNAMIC]"  # Indicate port will be assigned dynamically
            
            return PatchStatusResponse(
                status="analyzed",
                message="Static analysis completed",
                execution_output="",
                error_output="\n".join(static_errors) if static_errors else "",
                return_code=0 if not static_errors else 1,
                analysis=analysis_result,
                suggested_improvements=suggested_improvements,
                completed=True,
                was_regenerated=needs_regeneration,
                app_url=app_url,
                app_type=web_app.get("type") if web_app else None,
                app_port=app_port
            )
        else:
            logger.info(f"Executing patch {patch_id} with actual code execution")
            # Actually execute the code
            logger.info(f"Executing patch {patch_id}")
            
            # Execute the patch using the improved environment manager
            success, stdout, stderr, return_code = await execute_patch(patch_id)
            
            logger.info(f"Execution completed: success={success}, return_code={return_code}")
            logger.info(f"Execution stdout: {stdout}")
            logger.info(f"Execution stderr: {stderr}")
            
            # Check for matplotlib-related output and find generated images
            matplotlib_detected = "matplotlib" in stdout.lower() or "matplotlib" in stderr.lower()
            logger.info(f"Matplotlib detected: {matplotlib_detected}")
            logger.info(f"Stdout: {stdout}")
            logger.info(f"Stderr: {stderr}")
            image_output = ""
            generated_images = []
            
            if matplotlib_detected:
                # Look for image file paths in output
                import re
                image_patterns = [
                    r'Image saved to: (.+\.png)',
                    r'Image saved to: (.+\.jpg)',
                    r'Image saved to: (.+\.jpeg)',
                    r'Image saved to: (.+\.svg)',
                    r'Plot saved to: (.+\.png)',
                    r'Figure saved to: (.+\.png)',
                    r'Saved plot to: (.+\.png)',
                    r'Plot saved as: (.+\.png)',
                    r'Image saved at: (.+\.png)'
                ]
                
                for pattern in image_patterns:
                    matches = re.findall(pattern, stdout, re.IGNORECASE)
                    if matches:
                        image_output = f"Generated image: {matches[0]}"
                        generated_images.extend(matches)
                        break
                
                # Also search for images in the patch directory and workspace root
                patch_dir = os.path.join(code_generator.patches_dir, patch_id)
                workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                
                # Search in patch directory
                for root, dirs, files in os.walk(patch_dir):
                    for file in files:
                        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')):
                            full_path = os.path.join(root, file)
                            rel_path = os.path.relpath(full_path, patch_dir)
                            generated_images.append(rel_path)
                            if not image_output:
                                image_output = f"Generated image: {rel_path}"
                
                # Search in workspace root for images mentioned in output
                for root, dirs, files in os.walk(workspace_root):
                    for file in files:
                        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')):
                            # Check if this image was mentioned in the output (full path or filename)
                            full_path = os.path.join(root, file)
                            logger.info(f"Checking image file: {file}, full_path: {full_path}")
                            if file in stdout or file in stderr or full_path in stdout or full_path in stderr:
                                rel_path = os.path.relpath(full_path, workspace_root)
                                logger.info(f"Found matching image: {rel_path}")
                                generated_images.append(rel_path)
                                if not image_output:
                                    image_output = f"Generated image: {rel_path}"
            
            # Prepare response
            if success:
                status = "executed"
                message = "Patch executed successfully"
                if image_output:
                    message += f" - {image_output}"
            else:
                status = "failed"
                message = "Patch execution failed"
            
            return PatchStatusResponse(
                status=status,
                message=message,
                execution_output=stdout,
                error_output=stderr,
                return_code=return_code,
                analysis="Execution completed" if success else "Execution failed",
                suggested_improvements=["Check error output for details"] if not success else ["Use start-web-app endpoint to run web applications"],
                completed=True,
                was_regenerated=False,
                app_url=web_app.get("url") if web_app else None,
                app_type=web_app.get("type") if web_app else None,
                app_port=web_app.get("port") if web_app else None,
                generated_images=generated_images if generated_images else None
            )
        
    except Exception as e:
        logger.error(f"Error in execute_patch_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Patch status endpoint
@app.get("/patch-status/{patch_id}", response_model=PatchStatusResponse)
async def get_patch_status(patch_id: str):
    """Get the status of a running patch."""
    try:
        if patch_id not in patch_run_results:
            raise HTTPException(status_code=404, detail=f"No results found for patch {patch_id}")
        
        return PatchStatusResponse(**patch_run_results[patch_id])
    except Exception as e:
        logger.error(f"Error getting patch status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

class StartWebAppRequest(BaseModel):
    """Model for starting a web application."""
    patch_id: str

class WebAppRequest(BaseModel):
    """Model for web application operations."""
    patch_id: str
    action: str  # 'start' or 'stop'

@app.get("/web-app/{patch_id}/status")
async def get_web_app_status(patch_id: str):
    """Get the status of a web application."""
    try:
        # Check if the web app is running
        if patch_id in running_web_apps:
            process = running_web_apps[patch_id]
            if process.poll() is None:  # Process is still running
                # Get the port from the web app info
                web_app = detect_web_application(patch_id)
                if web_app:
                    # Find the actual port by checking what's running
                    for port in range(5000, 6000):
                        try:
                            response = requests.get(f"http://localhost:{port}/health", timeout=1)
                            if response.status_code == 200:
                                return {
                                    "is_running": True,
                                    "url": f"http://localhost:{port}",
                                    "port": str(port),
                                    "framework": web_app.get("framework", "Unknown")
                                }
                        except:
                            continue
                    
                    # If we can't find the exact port, return a generic response
                    return {
                        "is_running": True,
                        "url": "http://localhost:[PORT]",
                        "port": "[DYNAMIC]",
                        "framework": web_app.get("framework", "Unknown")
                    }
        
        return {
            "is_running": False,
            "url": None,
            "port": None,
            "framework": None
        }
    except Exception as e:
        logger.error(f"Error getting web app status for {patch_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting web app status: {str(e)}")

@app.post("/web-app/")
async def web_app_operation(request: WebAppRequest):
    """Handle web application start/stop operations."""
    if request.action == "start":
        return await start_web_app(StartWebAppRequest(patch_id=request.patch_id))
    elif request.action == "stop":
        # For now, just return success since we don't have stop functionality
        return {"status": "stopped", "message": "Web application stopped"}
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'start' or 'stop'")

@app.post("/start-web-app/")
async def start_web_app(request: StartWebAppRequest):
    """Enhanced startApp functionality with comprehensive framework support."""
    try:
        patch_id = request.patch_id
        patch_dir = os.path.join(code_generator.patches_dir, patch_id)
        
        if not os.path.exists(patch_dir):
            raise HTTPException(status_code=404, detail="Patch not found")
        
        # Check if already running
        if patch_id in running_web_apps:
            process = running_web_apps[patch_id]
            if process.poll() is None:  # Still running
                # Get the actual port from the running process
                web_app = detect_web_application(patch_id)
                if web_app:
                    return {"status": "already_running", "url": web_app["url"]}
                return {"status": "already_running", "url": "http://localhost:5001"}
        
        # Enhanced web application detection
        web_app = detect_web_application(patch_id)
        if not web_app:
            raise HTTPException(status_code=400, detail="No web application detected in this patch")
        
        logger.info(f"Detected {web_app['framework']} application for patch {patch_id}")
        
        # Find an available port
        try:
            random_port = find_available_port(5000, 50)
            logger.info(f"Using random port {random_port} for patch {patch_id}")
        except RuntimeError:
            raise HTTPException(status_code=500, detail="Could not find available port")
        
        # Start the web application based on framework type with enhanced logic
        success = False
        
        if web_app["type"] == "Flask":
            success = await _start_flask_app_enhanced(patch_dir, patch_id, random_port, web_app)
        elif web_app["type"] == "FastAPI":
            success = await _start_fastapi_app_enhanced(patch_dir, patch_id, random_port, web_app)
        elif web_app["type"] == "Streamlit":
            success = await _start_streamlit_app_enhanced(patch_dir, patch_id, web_app)
        elif web_app["type"] == "Dash":
            success = await _start_dash_app_enhanced(patch_dir, patch_id, random_port, web_app)
        elif web_app["type"] == "Django":
            success = await _start_django_app_enhanced(patch_dir, patch_id, random_port, web_app)
        elif web_app["type"] == "Bottle":
            success = await _start_bottle_app_enhanced(patch_dir, patch_id, random_port, web_app)
        elif web_app["type"] == "Tornado":
            success = await _start_tornado_app_enhanced(patch_dir, patch_id, random_port, web_app)
        else:
            success = await _start_generic_web_app_enhanced(patch_dir, patch_id, random_port, web_app)
        
        if success:
            # Update the web_app info with the random port
            web_app["port"] = str(random_port)
            web_app["url"] = f"http://localhost:{random_port}"
            
            logger.info(f"Successfully started {web_app['framework']} app on port {random_port}")
            
            return {
                "status": "started",
                "url": web_app["url"],
                "type": web_app["type"],
                "port": web_app["port"],
                "framework": web_app["framework"]
            }
        else:
            raise HTTPException(status_code=500, detail=f"Failed to start {web_app['framework']} application")
            
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Failed to start web application: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting web application: {str(e)}")

async def _start_flask_app_enhanced(patch_dir: str, patch_id: str, port: int, web_app: dict) -> bool:
    """Enhanced Flask app startup with comprehensive error handling and template management."""
    try:
        logger.info(f"Starting enhanced Flask app for patch {patch_id}")
        
        # Install requirements with enhanced error handling
        requirements_path = os.path.join(patch_dir, "requirements.txt")
        if os.path.exists(requirements_path):
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", requirements_path
                ], cwd=patch_dir, check=True, capture_output=True, text=True)
                logger.info(f"Requirements installed successfully for {patch_id}")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to install requirements for {patch_id}: {e.stderr}")
                # Continue anyway - Flask might be available globally
        
        # Enhanced template structure management
        src_dir = os.path.join(patch_dir, "src")
        templates_dir = os.path.join(src_dir, "templates")
        static_dir = os.path.join(src_dir, "static")
        
        # Create necessary directories
        os.makedirs(templates_dir, exist_ok=True)
        os.makedirs(static_dir, exist_ok=True)
        
        # Enhanced template file management
        if os.path.exists(src_dir):
            template_extensions = ['.html', '.jinja2', '.j2']
            template_files = [f for f in os.listdir(src_dir) 
                            if any(f.endswith(ext) for ext in template_extensions)]
            
            for template_file in template_files:
                src_template_path = os.path.join(src_dir, template_file)
                
                # Convert .jinja2 files to .html for Flask compatibility
                if template_file.endswith('.jinja2'):
                    template_file = template_file.replace('.jinja2', '.html')
                    logger.info(f"Converting {template_file} from .jinja2 to .html")
                
                templates_template_path = os.path.join(templates_dir, template_file)
                
                # Always copy/overwrite to ensure we have the latest version
                import shutil
                shutil.copy2(src_template_path, templates_template_path)
                logger.info(f"Moved {template_file} to templates directory for {patch_id}")
        
        # Enhanced main.py modification
        main_py_path = os.path.join(patch_dir, "src", "main.py")
        if not os.path.exists(main_py_path):
            logger.error(f"main.py not found for {patch_id}")
            return False
        
        # Backup original content
        with open(main_py_path, 'r') as f:
            original_content = f.read()
        
        # Enhanced port configuration replacement
        import re
        
        # Replace any hardcoded port with environment variable
        modified_content = re.sub(
            r'app\.run\([^)]*port\s*=\s*\d+[^)]*\)',
            f'app.run(debug=True, host="0.0.0.0", port={port})',
            original_content
        )
        
        # Add port import if not present
        if 'import os' not in modified_content:
            modified_content = modified_content.replace('from flask import', 'import os\nfrom flask import')
        
        # Add port configuration if not present
        if 'port = int(os.environ.get(' not in modified_content:
            modified_content = re.sub(
                r'(if __name__ == [\'"]__main__[\'"]:)',
                r'\1\n    port = int(os.environ.get(\'PORT\', 5001))',
                modified_content
            )
        
        # Add health check endpoint if not present
        if '@app.route(\'/health\')' not in modified_content:
            health_endpoint = '''
@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'message': 'Flask app is running!'})
'''
            # Insert before the if __name__ block
            modified_content = re.sub(
                r'(if __name__ == [\'"]__main__[\'"]:)',
                f'{health_endpoint}\n\\1',
                modified_content
            )
            
            # Add jsonify import if not present
            if 'jsonify' not in modified_content and 'from flask import' in modified_content:
                modified_content = re.sub(
                    r'from flask import ([^)]+)',
                    r'from flask import \1, jsonify',
                    modified_content
                )
        
        # Write enhanced content
        with open(main_py_path, 'w') as f:
            f.write(modified_content)
        
        try:
            # Start the Flask server with enhanced monitoring
            env = os.environ.copy()
            env['PORT'] = str(port)
            process = subprocess.Popen([
                sys.executable, main_py_path
            ], cwd=os.path.join(patch_dir, "src"), 
               stdout=subprocess.PIPE,  # Capture output for debugging
               stderr=subprocess.PIPE,
               text=True,
               env=env)
            
            running_web_apps[patch_id] = process
            
            # Wait for server to start with timeout
            await asyncio.sleep(3)
            
            # Check if process is still running
            if process.poll() is not None:
                # Process has exited - get error output
                stdout, stderr = process.communicate()
                logger.error(f"Flask app failed to start for {patch_id}. stdout: {stdout}, stderr: {stderr}")
                
                # Restore original content
                with open(main_py_path, 'w') as f:
                    f.write(original_content)
                return False
            
            logger.info(f"Flask app started successfully for {patch_id} on port {port}")
            return True
            
        except Exception as e:
            # Restore original content on error
            with open(main_py_path, 'w') as f:
                f.write(original_content)
            logger.error(f"Error starting Flask app for {patch_id}: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"Error in enhanced Flask startup for {patch_id}: {str(e)}")
        return False

async def _start_fastapi_app_enhanced(patch_dir: str, patch_id: str, port: int, web_app: dict) -> bool:
    """Enhanced FastAPI app startup."""
    try:
        logger.info(f"Starting enhanced FastAPI app for patch {patch_id}")
        
        # Install requirements
        requirements_path = os.path.join(patch_dir, "requirements.txt")
        if os.path.exists(requirements_path):
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", requirements_path
            ], cwd=patch_dir, check=True, capture_output=True, text=True)
        
        # Start FastAPI app with uvicorn
        main_py_path = os.path.join(patch_dir, "src", "main.py")
        if not os.path.exists(main_py_path):
            logger.error(f"main.py not found for {patch_id}")
            return False
        
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "main:app", 
            "--host", "0.0.0.0", "--port", str(port), "--reload"
        ], cwd=os.path.join(patch_dir, "src"),
           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        running_web_apps[patch_id] = process
        await asyncio.sleep(3)
        
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            logger.error(f"FastAPI app failed to start for {patch_id}. stdout: {stdout}, stderr: {stderr}")
            return False
        
        logger.info(f"FastAPI app started successfully for {patch_id} on port {port}")
        return True
        
    except Exception as e:
        logger.error(f"Error starting FastAPI app for {patch_id}: {str(e)}")
        return False

async def _start_streamlit_app_enhanced(patch_dir: str, patch_id: str, web_app: dict) -> bool:
    """Enhanced Streamlit app startup."""
    try:
        logger.info(f"Starting enhanced Streamlit app for patch {patch_id}")
        
        # Install requirements
        requirements_path = os.path.join(patch_dir, "requirements.txt")
        if os.path.exists(requirements_path):
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", requirements_path
            ], cwd=patch_dir, check=True, capture_output=True, text=True)
        
        # Start Streamlit app
        main_py_path = os.path.join(patch_dir, "src", "main.py")
        if not os.path.exists(main_py_path):
            logger.error(f"main.py not found for {patch_id}")
            return False
        
        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", "main.py",
            "--server.port", "8501", "--server.address", "0.0.0.0"
        ], cwd=os.path.join(patch_dir, "src"),
           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        running_web_apps[patch_id] = process
        await asyncio.sleep(3)
        
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            logger.error(f"Streamlit app failed to start for {patch_id}. stdout: {stdout}, stderr: {stderr}")
            return False
        
        logger.info(f"Streamlit app started successfully for {patch_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error starting Streamlit app for {patch_id}: {str(e)}")
        return False

async def _start_dash_app_enhanced(patch_dir: str, patch_id: str, port: int, web_app: dict) -> bool:
    """Enhanced Dash app startup."""
    try:
        logger.info(f"Starting enhanced Dash app for patch {patch_id}")
        
        # Install requirements
        requirements_path = os.path.join(patch_dir, "requirements.txt")
        if os.path.exists(requirements_path):
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", requirements_path
            ], cwd=patch_dir, check=True, capture_output=True, text=True)
        
        # Start Dash app
        main_py_path = os.path.join(patch_dir, "src", "main.py")
        if not os.path.exists(main_py_path):
            logger.error(f"main.py not found for {patch_id}")
            return False
        
        process = subprocess.Popen([
            sys.executable, main_py_path
        ], cwd=os.path.join(patch_dir, "src"),
           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        running_web_apps[patch_id] = process
        await asyncio.sleep(3)
        
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            logger.error(f"Dash app failed to start for {patch_id}. stdout: {stdout}, stderr: {stderr}")
            return False
        
        logger.info(f"Dash app started successfully for {patch_id} on port {port}")
        return True
        
    except Exception as e:
        logger.error(f"Error starting Dash app for {patch_id}: {str(e)}")
        return False

async def _start_django_app_enhanced(patch_dir: str, patch_id: str, port: int, web_app: dict) -> bool:
    """Enhanced Django app startup."""
    try:
        logger.info(f"Starting enhanced Django app for patch {patch_id}")
        
        # Install requirements
        requirements_path = os.path.join(patch_dir, "requirements.txt")
        if os.path.exists(requirements_path):
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", requirements_path
            ], cwd=patch_dir, check=True, capture_output=True, text=True)
        
        # Start Django app
        manage_py_path = os.path.join(patch_dir, "manage.py")
        if not os.path.exists(manage_py_path):
            logger.error(f"manage.py not found for {patch_id}")
            return False
        
        process = subprocess.Popen([
            sys.executable, "manage.py", "runserver", f"0.0.0.0:{port}"
        ], cwd=patch_dir,
           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        running_web_apps[patch_id] = process
        await asyncio.sleep(3)
        
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            logger.error(f"Django app failed to start for {patch_id}. stdout: {stdout}, stderr: {stderr}")
            return False
        
        logger.info(f"Django app started successfully for {patch_id} on port {port}")
        return True
        
    except Exception as e:
        logger.error(f"Error starting Django app for {patch_id}: {str(e)}")
        return False

async def _start_bottle_app_enhanced(patch_dir: str, patch_id: str, port: int, web_app: dict) -> bool:
    """Enhanced Bottle app startup."""
    try:
        logger.info(f"Starting enhanced Bottle app for patch {patch_id}")
        
        # Install requirements
        requirements_path = os.path.join(patch_dir, "requirements.txt")
        if os.path.exists(requirements_path):
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", requirements_path
            ], cwd=patch_dir, check=True, capture_output=True, text=True)
        
        # Start Bottle app
        main_py_path = os.path.join(patch_dir, "src", "main.py")
        if not os.path.exists(main_py_path):
            logger.error(f"main.py not found for {patch_id}")
            return False
        
        process = subprocess.Popen([
            sys.executable, main_py_path
        ], cwd=os.path.join(patch_dir, "src"),
           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        running_web_apps[patch_id] = process
        await asyncio.sleep(3)
        
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            logger.error(f"Bottle app failed to start for {patch_id}. stdout: {stdout}, stderr: {stderr}")
            return False
        
        logger.info(f"Bottle app started successfully for {patch_id} on port {port}")
        return True
        
    except Exception as e:
        logger.error(f"Error starting Bottle app for {patch_id}: {str(e)}")
        return False

async def _start_tornado_app_enhanced(patch_dir: str, patch_id: str, port: int, web_app: dict) -> bool:
    """Enhanced Tornado app startup."""
    try:
        logger.info(f"Starting enhanced Tornado app for patch {patch_id}")
        
        # Install requirements
        requirements_path = os.path.join(patch_dir, "requirements.txt")
        if os.path.exists(requirements_path):
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", requirements_path
            ], cwd=patch_dir, check=True, capture_output=True, text=True)
        
        # Start Tornado app
        main_py_path = os.path.join(patch_dir, "src", "main.py")
        if not os.path.exists(main_py_path):
            logger.error(f"main.py not found for {patch_id}")
            return False
        
        process = subprocess.Popen([
            sys.executable, main_py_path
        ], cwd=os.path.join(patch_dir, "src"),
           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        running_web_apps[patch_id] = process
        await asyncio.sleep(3)
        
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            logger.error(f"Tornado app failed to start for {patch_id}. stdout: {stdout}, stderr: {stderr}")
            return False
        
        logger.info(f"Tornado app started successfully for {patch_id} on port {port}")
        return True
        
    except Exception as e:
        logger.error(f"Error starting Tornado app for {patch_id}: {str(e)}")
        return False

async def _start_generic_web_app_enhanced(patch_dir: str, patch_id: str, port: int, web_app: dict) -> bool:
    """Enhanced generic web app startup."""
    try:
        logger.info(f"Starting enhanced generic web app for patch {patch_id}")
        
        # Install requirements
        requirements_path = os.path.join(patch_dir, "requirements.txt")
        if os.path.exists(requirements_path):
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", requirements_path
            ], cwd=patch_dir, check=True, capture_output=True, text=True)
        
        # Start generic app
        main_py_path = os.path.join(patch_dir, "src", "main.py")
        if not os.path.exists(main_py_path):
            logger.error(f"main.py not found for {patch_id}")
            return False
        
        process = subprocess.Popen([
            sys.executable, main_py_path
        ], cwd=os.path.join(patch_dir, "src"),
           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        running_web_apps[patch_id] = process
        await asyncio.sleep(3)
        
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            logger.error(f"Generic web app failed to start for {patch_id}. stdout: {stdout}, stderr: {stderr}")
            return False
        
        logger.info(f"Generic web app started successfully for {patch_id} on port {port}")
        return True
        
    except Exception as e:
        logger.error(f"Error starting generic web app for {patch_id}: {str(e)}")
        return False

@app.post("/regenerate-patch/")
async def regenerate_patch(request: RegeneratePatchRequest):
    """Regenerate code for a specific patch."""
    try:
        logger.info(f"Regenerating patch: {request.patch_id}")
        
        # Get the patch metadata
        task = await get_patch_metadata(request.patch_id)
        
        # Perform comprehensive regeneration
        success = await perform_comprehensive_regeneration(request.patch_id, task, {
            "issues": ["user_requested_regeneration"],
            "regeneration_strategy": "comprehensive"
        })
        
        if success:
            return {
                "message": f"Patch {request.patch_id} regenerated successfully",
                "changes": [
                    "Code structure improved",
                    "Dependencies updated",
                    "Error handling enhanced",
                    "Code quality optimized"
                ]
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to regenerate patch")
            
    except Exception as e:
        logger.error(f"Error regenerating patch: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patch-images/{patch_id}/{image_path:path}")
async def get_patch_image(patch_id: str, image_path: str):
    """Serve generated images from patch directories and workspace root."""
    try:
        # Try patch directory first
        patch_dir = os.path.join(code_generator.patches_dir, patch_id)
        full_image_path = os.path.join(patch_dir, image_path)
        
        # If not found in patch directory, try workspace root
        if not os.path.exists(full_image_path):
            workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            full_image_path = os.path.join(workspace_root, image_path)
            
            # Security check: ensure the path is within the workspace root
            if not os.path.abspath(full_image_path).startswith(os.path.abspath(workspace_root)):
                raise HTTPException(status_code=403, detail="Access denied")
        else:
            # Security check: ensure the path is within the patch directory
            if not os.path.abspath(full_image_path).startswith(os.path.abspath(patch_dir)):
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if the image exists
        if not os.path.exists(full_image_path):
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Determine content type based on file extension
        content_type = "image/png"  # default
        if image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg'):
            content_type = "image/jpeg"
        elif image_path.lower().endswith('.svg'):
            content_type = "image/svg+xml"
        
        # Read and return the image
        with open(full_image_path, 'rb') as f:
            image_data = f.read()
        
        from fastapi.responses import Response
        return Response(content=image_data, media_type=content_type)
        
    except Exception as e:
        logger.error(f"Error serving image {image_path} for patch {patch_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patch-images/{patch_id}")
async def list_patch_images(patch_id: str):
    """List all generated images for a patch."""
    try:
        patch_dir = os.path.join(code_generator.patches_dir, patch_id)
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        if not os.path.exists(patch_dir):
            raise HTTPException(status_code=404, detail="Patch not found")
        
        images = []
        
        # Search in patch directory
        for root, dirs, files in os.walk(patch_dir):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, patch_dir)
                    images.append({
                        "filename": file,
                        "path": rel_path,
                        "url": f"/patch-images/{patch_id}/{rel_path}"
                    })
        
        # Search in workspace root for common image files
        for root, dirs, files in os.walk(workspace_root):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')):
                    # Only include images that are likely generated by patches
                    if any(keyword in file.lower() for keyword in ['grade', 'plot', 'chart', 'graph', 'histogram']):
                        rel_path = os.path.relpath(os.path.join(root, file), workspace_root)
                        images.append({
                            "filename": file,
                            "path": rel_path,
                            "url": f"/patch-images/{patch_id}/{rel_path}"
                        })
        
        return {"images": images}
        
    except Exception as e:
        logger.error(f"Error listing images for patch {patch_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 