import os
import subprocess
import sys
import traceback
import json
import requests
import pytest
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

def test_patch_execution(patch_id: str):
    """Test executing a patch's code directly."""
    try:
        print("\n=== Starting Test ===")
        
        # Get the absolute path to the workspace root (where project/ directory is)
        workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        print(f"Workspace root: {workspace_root}")
        
        # Construct patch directory path
        patch_dir = os.path.join(workspace_root, "project", "patches", patch_id)
        print(f"Looking for patch in: {patch_dir}")
        
        if not os.path.exists(patch_dir):
            print(f"ERROR: Patch directory not found at {patch_dir}")
            return False, f"Patch directory not found: {patch_id}"
                
        # Run the code
        src_dir = os.path.join(patch_dir, "src")
        print(f"Source directory: {src_dir}")
        
        if not os.path.exists(src_dir):
            print(f"ERROR: Source directory not found at {src_dir}")
            return False, "Source directory not found"
        
        files = os.listdir(src_dir)
        print(f"Files in source directory: {files}")
        
        if not files:
            print("ERROR: No files found in source directory")
            return False, "No files found in source directory"
            
        main_file = files[0]
        main_file_path = os.path.join(src_dir, main_file)
        print(f"Found main file: {main_file}")
        print(f"Full path: {main_file_path}")
        
        print("\n=== Executing Code ===")
        process = subprocess.Popen(
            [sys.executable, main_file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=src_dir  # Set working directory to src directory
        )
        print("Process started, waiting for output...")
        output, error_output = process.communicate()
        
        execution_success = process.returncode == 0
        execution_output = output if execution_success else f"Error: {error_output}"
        
        print("\n=== Execution Results ===")
        print(f"Return Code: {process.returncode}")
        print(f"Success: {execution_success}")
        print("Standard Output:")
        print("---")
        print(output or "No output")
        print("---")
        if error_output:
            print("Error Output:")
            print("---")
            print(error_output)
            print("---")
        
        return execution_success, execution_output

    except Exception as e:
        print("\n=== Exception Occurred ===")
        print("Error:", str(e))
        print("Traceback:")
        traceback.print_exc()
        return False, str(e)

def test_student_grades_regeneration():
    """Test that the student grades code triggers RAG regeneration."""
    
    # Path to the patch
    patch_id = "20250706_153824_create_a_function_to_process_student_grades"
    
    # Call the execute-patch endpoint
    response = requests.post(
        "http://localhost:8000/execute-patch/",
        json={"patch_id": patch_id}
    )
    
    assert response.status_code == 200, f"Failed to execute patch: {response.text}"
    
    result = response.json()
    print("\nExecution Result:")
    print(json.dumps(result, indent=2))
    
    # Verify regeneration was triggered
    assert result.get("was_regenerated", False), \
        "Code regeneration was not triggered"
    
    # Verify the regenerated code works
    if result.get("was_regenerated"):
        # Re-run to test the improved code
        response = requests.post(
            "http://localhost:8000/execute-patch/",
            json={"patch_id": patch_id}
        )
        
        improved_result = response.json()
        print("\nRe-execution Result:")
        print(json.dumps(improved_result, indent=2))
        
        # Verify the improved code handles edge cases
        assert improved_result.get("return_code") == 0, \
            "Regenerated code still has errors"
        assert "Error processing grades" not in improved_result.get("error_output", "") and \
               "Error processing grades" not in improved_result.get("execution_output", ""), \
            "Regenerated code still throws errors"

if __name__ == "__main__":
    test_student_grades_regeneration() 