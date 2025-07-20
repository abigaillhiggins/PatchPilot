import os
import sys
import subprocess
import shutil
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class IsolatedEnvironment:
    def __init__(self, patch_dir: str):
        self.patch_dir = patch_dir
        self.venv_path = os.path.join(patch_dir, "venv")
        self.python_path = os.path.join(self.venv_path, "bin", "python")
        self.pip_path = os.path.join(self.venv_path, "bin", "pip")
        
    def create(self) -> bool:
        """Create a new virtual environment."""
        try:
            logger.info(f"Creating virtual environment in {self.venv_path}")
            subprocess.run(
                [sys.executable, "-m", "venv", self.venv_path],
                check=True,
                capture_output=True,
                text=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create virtual environment: {e.stderr}")
            return False
            
    def install_requirements(self) -> bool:
        """Install requirements from requirements.txt."""
        req_path = os.path.join(self.patch_dir, "requirements.txt")
        if not os.path.exists(req_path):
            logger.warning(f"No requirements.txt found in {self.patch_dir}")
            return True
            
        try:
            logger.info("Installing requirements...")
            subprocess.run(
                [self.pip_path, "install", "-r", req_path],
                check=True,
                capture_output=True,
                text=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install requirements: {e.stderr}")
            return False
            
    def run_script(self, script_path: str) -> tuple[bool, str, str, int]:
        """Run a Python script in the isolated environment."""
        try:
            logger.info(f"Running {script_path} in isolated environment")
            
            # Ensure proper Flask template structure if this is a Flask app
            script_dir = os.path.dirname(script_path)
            if os.path.exists(os.path.join(script_dir, "main.py")):
                # Check if this looks like a Flask app
                with open(os.path.join(script_dir, "main.py"), 'r') as f:
                    content = f.read()
                    if "from flask import" in content or "Flask(" in content:
                        # Ensure templates directory exists
                        templates_dir = os.path.join(script_dir, "templates")
                        if not os.path.exists(templates_dir):
                            os.makedirs(templates_dir, exist_ok=True)
                        
                        # Move template files to templates directory
                        template_extensions = ['.html', '.jinja2', '.j2']
                        template_files = [f for f in os.listdir(script_dir) 
                                        if any(f.endswith(ext) for ext in template_extensions)]
                        
                        for template_file in template_files:
                            src_template_path = os.path.join(script_dir, template_file)
                            
                            # Convert .jinja2 files to .html for Flask compatibility
                            if template_file.endswith('.jinja2'):
                                template_file = template_file.replace('.jinja2', '.html')
                                logger.info(f"Converting {template_file} from .jinja2 to .html")
                            
                            templates_template_path = os.path.join(templates_dir, template_file)
                            
                            if not os.path.exists(templates_template_path):
                                shutil.copy2(src_template_path, templates_template_path)
                                logger.info(f"Moved {template_file} to templates directory")
            
            # Set environment variable to indicate patch execution mode
            env = os.environ.copy()
            env['PATCH_EXECUTION'] = '1'
            
            process = subprocess.run(
                [self.python_path, script_path],
                capture_output=True,
                text=True,
                env=env
            )
            return (
                process.returncode == 0,
                process.stdout,
                process.stderr,
                process.returncode
            )
        except Exception as e:
            logger.error(f"Failed to run script: {str(e)}")
            return False, "", str(e), 1
            
    def cleanup(self) -> bool:
        """Remove the virtual environment."""
        try:
            if os.path.exists(self.venv_path):
                logger.info(f"Cleaning up virtual environment: {self.venv_path}")
                shutil.rmtree(self.venv_path)
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup virtual environment: {str(e)}")
            return False 