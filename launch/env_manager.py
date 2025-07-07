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
            process = subprocess.run(
                [self.python_path, script_path],
                capture_output=True,
                text=True
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