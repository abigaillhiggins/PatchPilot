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
    
    def _detect_matplotlib_usage(self, script_path: str) -> bool:
        """Detect if the script uses matplotlib."""
        try:
            with open(script_path, 'r') as f:
                content = f.read().lower()
                return any(keyword in content for keyword in [
                    'import matplotlib',
                    'from matplotlib',
                    'matplotlib.pyplot',
                    'plt.show',
                    'plt.figure',
                    'plt.plot',
                    'plt.hist'
                ])
        except Exception:
            return False
    
    def _create_matplotlib_wrapper(self, script_path: str) -> str:
        """Create a wrapper script that configures matplotlib for interactive or headless environment."""
        wrapper_content = f'''#!/usr/bin/env python3
import os
import sys

# Simple environment detection for matplotlib
def can_display_gui():
    """Check if we can display GUI windows."""
    # Check for display environment variables
    if os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'):
        return True
    
    # On macOS, we can usually display GUI
    if sys.platform == 'darwin':
        return True
    
    return False

# Set matplotlib backend
if can_display_gui():
    try:
        os.environ['MPLBACKEND'] = 'TkAgg'
        print("Running in interactive environment - using TkAgg backend")
        print("Plot window should appear - close it to continue")
    except:
        os.environ['MPLBACKEND'] = 'Agg'
        print("Interactive backend not available - saving plot to file")
else:
    os.environ['MPLBACKEND'] = 'Agg'
    print("Running in headless environment - saving plot to file")

# Import and run the original script
exec(open(r'{script_path}').read())
'''
        
        wrapper_path = script_path + '.wrapper.py'
        with open(wrapper_path, 'w') as f:
            f.write(wrapper_content)
        
        return wrapper_path
            
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
            
            # Check if matplotlib is used and create wrapper if needed
            uses_matplotlib = self._detect_matplotlib_usage(script_path)
            actual_script_path = script_path
            
            if uses_matplotlib:
                logger.info("Matplotlib detected - creating headless environment wrapper")
                actual_script_path = self._create_matplotlib_wrapper(script_path)
            
            # Set up environment for execution
            env = os.environ.copy()
            
            # Only set PATCH_EXECUTION for non-interactive matplotlib scripts
            if uses_matplotlib:
                # Check if we can support interactive display
                display_vars = ['DISPLAY', 'WAYLAND_DISPLAY', 'MIR_SOCKET']
                has_display = any(env.get(var) for var in display_vars)
                is_macos = sys.platform == 'darwin'
                
                if has_display or is_macos:
                    # Interactive environment - don't set PATCH_EXECUTION
                    logger.info("Matplotlib detected - attempting interactive display")
                else:
                    # Headless environment
                    env['PATCH_EXECUTION'] = '1'
                    logger.info("Matplotlib detected - using headless mode")
            else:
                # Non-matplotlib script
                env['PATCH_EXECUTION'] = '1'
            
            process = subprocess.run(
                [self.python_path, actual_script_path],
                capture_output=True,
                text=True,
                env=env
            )
            
            # Clean up wrapper if created
            if uses_matplotlib and actual_script_path != script_path:
                try:
                    os.remove(actual_script_path)
                except:
                    pass
            
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