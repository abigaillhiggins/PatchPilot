import requests
import json
import time
import argparse
from typing import Dict, Optional

def get_base_url(port: int = 8000) -> str:
    """Get the base URL for the API."""
    return f"http://0.0.0.0:{port}"

def create_todo(title: str, description: str, language: str, requirements: list, port: int = 8000) -> Optional[Dict]:
    """Create a new todo item."""
    data = {
        "title": title,
        "description": description,
        "language": language,
        "requirements": requirements
    }
    
    print(f"\n📝 Creating todo: {title}")
    response = requests.post(f"{get_base_url(port)}/todos", json=data)
    if response.status_code == 200:
        result = response.json()
        print("✅ Todo created successfully!")
        print(json.dumps(result, indent=2))
        return result
    else:
        print(f"❌ Failed to create todo: {response.text}")
        return None

def generate_code(todo_id: int, port: int = 8000) -> Optional[Dict]:
    """Generate code for a todo item."""
    print(f"\n🔨 Generating code for todo {todo_id}")
    response = requests.post(f"{get_base_url(port)}/generate-code/{todo_id}")
    if response.status_code == 200:
        result = response.json()
        print("✅ Code generated successfully!")
        print(json.dumps(result, indent=2))
        return result
    else:
        print(f"❌ Failed to generate code: {response.text}")
        return None

def get_todo(todo_id: int, port: int = 8000) -> Optional[Dict]:
    """Get a todo item by ID."""
    response = requests.get(f"{get_base_url(port)}/todos/{todo_id}")
    if response.status_code == 200:
        return response.json()
    return None

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test autonomous code generation')
    parser.add_argument('--port', type=int, default=8000, help='Port number (default: 8000)')
    args = parser.parse_args()
    
    # Test 1: Create and generate simple utility function
    print("\n🧪 Test 1: Simple Utility Function")
    todo1 = create_todo(
        title="Create array utility functions",
        description="Create utility functions for array operations",
        language="python",
        requirements=[
            "Implement array reversal",
            "Implement finding maximum element",
            "Add type hints",
            "Include unit tests"
        ],
        port=args.port
    )
    if todo1:
        time.sleep(1)  # Give the system time to process
        generate_code(todo1["id"], port=args.port)
    
    # Test 2: Create and generate class with error handling
    print("\n🧪 Test 2: Class with Error Handling")
    todo2 = create_todo(
        title="Create data validator class",
        description="Create a class for validating input data",
        language="python",
        requirements=[
            "Validate string length",
            "Check numeric ranges",
            "Handle missing fields",
            "Raise custom exceptions",
            "Include comprehensive error messages"
        ],
        port=args.port
    )
    if todo2:
        time.sleep(1)  # Give the system time to process
        generate_code(todo2["id"], port=args.port)
    
    # Test 3: Create and generate async function
    print("\n🧪 Test 3: Async Function")
    todo3 = create_todo(
        title="Create async data fetcher",
        description="Create an async function to fetch data from multiple sources",
        language="python",
        requirements=[
            "Fetch data asynchronously",
            "Handle timeouts",
            "Implement retry logic",
            "Add concurrent request limiting",
            "Include error handling"
        ],
        port=args.port
    )
    if todo3:
        time.sleep(1)  # Give the system time to process
        generate_code(todo3["id"], port=args.port)
    
    # Check final status of all todos
    print("\n📊 Final Status Check")
    for todo in [todo1, todo2, todo3]:
        if todo:
            status = get_todo(todo["id"], port=args.port)
            if status:
                print(f"\nTodo {todo['id']} - {todo['title']}:")
                print(f"Status: {status.get('completed', False)}")
                print(f"Patch ID: {status.get('patch_id', 'None')}")

if __name__ == "__main__":
    main() 