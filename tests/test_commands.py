import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_create_todo():
    """Test creating a new todo item"""
    data = {
        "title": "Create a simple calculator",
        "description": "Create a Python calculator with basic arithmetic operations",
        "language": "python",
        "requirements": [
            "Support addition, subtraction, multiplication, division",
            "Handle decimal numbers",
            "Include input validation",
            "Add unit tests"
        ]
    }
    
    response = requests.post(f"{BASE_URL}/todos", json=data)
    print("\nCreate Todo Response:", json.dumps(response.json(), indent=2))
    return response.json().get("id")

def test_generate_code(todo_id):
    """Test generating code for a todo item"""
    response = requests.post(f"{BASE_URL}/generate-code/{todo_id}")
    print("\nGenerate Code Response:", json.dumps(response.json(), indent=2))
    return response.json().get("patch_id")

def test_list_todos():
    """Test listing all todos"""
    response = requests.get(f"{BASE_URL}/todos")
    print("\nList Todos Response:", json.dumps(response.json(), indent=2))

def main():
    print("Testing API Commands...")
    
    # Create a new todo
    print("\n1. Creating a new todo...")
    todo_id = test_create_todo()
    
    if todo_id:
        # Generate code for the todo
        print("\n2. Generating code for the todo...")
        patch_id = test_generate_code(todo_id)
        
        # List all todos
        print("\n3. Listing all todos...")
        test_list_todos()
    else:
        print("Failed to create todo")

if __name__ == "__main__":
    main() 