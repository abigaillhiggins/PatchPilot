import os
import sys
import pytest
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from env_manager import IsolatedEnvironment

def test_isolated_environment(tmp_path):
    """Test the IsolatedEnvironment class."""
    # Create a test patch directory
    patch_dir = tmp_path / "test_patch"
    patch_dir.mkdir()
    
    # Create a test requirements.txt
    with open(patch_dir / "requirements.txt", "w") as f:
        f.write("pytest>=7.0.0\n")
    
    # Create a test script
    src_dir = patch_dir / "src"
    src_dir.mkdir()
    with open(src_dir / "test.py", "w") as f:
        f.write("""
import pytest
print("Test successful!")
""")
    
    # Test environment creation and cleanup
    env = IsolatedEnvironment(str(patch_dir))
    try:
        # Test environment creation
        assert env.create(), "Failed to create virtual environment"
        assert os.path.exists(env.venv_path), "Virtual environment directory not created"
        
        # Test requirements installation
        assert env.install_requirements(), "Failed to install requirements"
        
        # Test script execution
        success, stdout, stderr, return_code = env.run_script(str(src_dir / "test.py"))
        assert success, f"Script execution failed: {stderr}"
        assert "Test successful!" in stdout, "Expected output not found"
        assert return_code == 0, "Non-zero return code"
        
    finally:
        # Test cleanup
        assert env.cleanup(), "Failed to cleanup virtual environment"
        assert not os.path.exists(env.venv_path), "Virtual environment not properly cleaned up"

def test_isolated_environment_error_handling(tmp_path):
    """Test error handling in IsolatedEnvironment."""
    patch_dir = tmp_path / "test_patch"
    patch_dir.mkdir()
    
    env = IsolatedEnvironment(str(patch_dir))
    
    # Test running non-existent script
    success, stdout, stderr, return_code = env.run_script("nonexistent.py")
    assert not success, "Should fail when script doesn't exist"
    assert return_code != 0, "Should return non-zero code on failure"
    
    # Test invalid requirements
    with open(patch_dir / "requirements.txt", "w") as f:
        f.write("not-a-real-package==1.0.0\n")
    
    assert not env.install_requirements(), "Should fail with invalid requirement" 