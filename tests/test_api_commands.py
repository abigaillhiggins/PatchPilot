import requests
import json
import time
from typing import Dict, Any, Optional

class APITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an HTTP request to the API."""
        url = f"{self.base_url}/{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {str(e)}")
            return {"error": str(e)}

    def generate_code(self, description: str, language: str = "python", requirements: list = None) -> Dict[str, Any]:
        """Generate code using the /generate-code endpoint."""
        data = {
            "description": description,
            "language": language,
            "requirements": requirements or []
        }
        return self._make_request("POST", "generate-code", data)

    def execute_patch(self, patch_id: str) -> Dict[str, Any]:
        """Execute a patch using the fast execution endpoint."""
        data = {"patch_id": patch_id}
        return self._make_request("POST", "execute-patch", data)

    def run_patch_with_analysis(self, patch_id: str, analyze: bool = True) -> Dict[str, Any]:
        """Run a patch with optional analysis."""
        data = {
            "patch_id": patch_id,
            "analyze": analyze
        }
        initial_response = self._make_request("POST", "run-patch", data)
        
        # If processing asynchronously, poll for results
        if initial_response.get("status") == "processing":
            print("Waiting for analysis to complete...")
            while True:
                status = self._make_request("GET", f"patch-status/{patch_id}")
                if status.get("completed", False):
                    return status
                time.sleep(1)  # Wait 1 second between polls
                
        return initial_response

def test_calculator_suite():
    """Test suite for calculator operations."""
    tester = APITester()
    
    print("\n=== Testing Calculator Utility ===")
    
    # 1. Fast Execution Test
    print("\n1. Fast Execution Test:")
    result = tester.execute_patch("20250706_144116_create_a_calculator_utility")
    print(f"Status: {result.get('status')}")
    print(f"Return Code: {result.get('return_code')}")
    print("Output:")
    print(result.get('execution_output', ''))
    if result.get('error_output'):
        print("Errors:")
        print(result.get('error_output'))

    # 2. Run with Analysis
    print("\n2. Run with Analysis:")
    result = tester.run_patch_with_analysis("20250706_144116_create_a_calculator_utility")
    print(f"Success: {result.get('success')}")
    print("Output:")
    print(result.get('output', ''))
    if result.get('error_output'):
        print("Errors:")
        print(result.get('error_output'))
    if result.get('analysis'):
        print("\nAnalysis:")
        print(result.get('analysis'))
        if result.get('suggested_improvements'):
            print("\nSuggested Improvements:")
            for improvement in result.get('suggested_improvements', []):
                print(f"- {improvement}")

    # 3. Run without Analysis
    print("\n3. Run without Analysis:")
    result = tester.run_patch_with_analysis("20250706_144116_create_a_calculator_utility", analyze=False)
    print(f"Success: {result.get('success')}")
    print("Output:")
    print(result.get('output', ''))
    if result.get('error_output'):
        print("Errors:")
        print(result.get('error_output'))

def test_code_generation():
    """Test suite for code generation."""
    tester = APITester()
    
    print("\n=== Testing Code Generation ===")
    
    # Generate a simple utility
    description = "Create a string utility that can reverse strings and check if they are palindromes"
    requirements = [
        "Function to reverse a string",
        "Function to check if a string is a palindrome",
        "Include test cases",
        "Handle empty strings and special characters"
    ]
    
    print("\n1. Generating String Utility:")
    result = tester.generate_code(description, "python", requirements)
    print("Generated Code Path:", result.get('file_path'))
    print("Creation Time:", result.get('created_at'))
    
    # If code generation was successful, test the generated code
    if 'file_path' in result:
        patch_id = result['file_path'].split('/')[-2]  # Extract patch ID from path
        
        print("\n2. Testing Generated Code:")
        exec_result = tester.execute_patch(patch_id)
        print(f"Status: {exec_result.get('status')}")
        print(f"Return Code: {exec_result.get('return_code')}")
        print("Output:")
        print(exec_result.get('execution_output', ''))
        if exec_result.get('error_output'):
            print("Errors:")
            print(exec_result.get('error_output'))

if __name__ == "__main__":
    print("Starting API Test Suite...")
    
    # Test the calculator utility
    test_calculator_suite()
    
    # Test code generation
    test_code_generation()
    
    print("\nTest Suite Completed!") 