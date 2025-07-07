"""
Tests for the AutoCodeRover FastAPI server.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from server import app, db_manager
from models import TodoItem

# Initialize test client
client = TestClient(app)

# Test data
TEST_TODO = {
    "title": "Test todo",
    "description": "Test description"
}

TEST_CODE_REQUEST = {
    "description": "Create a simple hello world function",
    "language": "python",
    "requirements": ["Print 'Hello, World!'"],
    "context": "Basic example"
}

# Mock OpenAI response
MOCK_OPENAI_RESPONSE = MagicMock(
    choices=[
        MagicMock(
            message=MagicMock(
                content="""def hello_world():
    print('Hello, World!')

if __name__ == '__main__':
    hello_world()"""
            )
        )
    ]
)

@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Setup test environment and cleanup after tests."""
    # Setup: Use in-memory SQLite database for testing
    os.environ["DB_PATH"] = ":memory:"
    os.environ["PROJECT_DIR"] = "test_project"
    os.environ["OPENAI_KEY"] = "test_key"
    
    # Create test project directory
    os.makedirs("test_project", exist_ok=True)
    
    # Mock OpenAI client
    with patch('openai.OpenAI') as mock_openai:
        mock_client = MagicMock()
        mock_chat = MagicMock()
        mock_chat.completions.create.return_value = MOCK_OPENAI_RESPONSE
        mock_client.chat = mock_chat
        mock_openai.return_value = mock_client
        
        yield
    
    # Cleanup
    db_manager.close()
    if os.path.exists("test_project"):
        import shutil
        shutil.rmtree("test_project")

def test_create_todo():
    """Test creating a new todo."""
    response = client.post("/todos/", json=TEST_TODO)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == TEST_TODO["title"]
    assert data["description"] == TEST_TODO["description"]
    assert not data["completed"]
    assert "id" in data
    assert "created_at" in data

def test_list_todos():
    """Test listing all todos."""
    # Create a todo first
    client.post("/todos/", json=TEST_TODO)
    
    response = client.get("/todos/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["title"] == TEST_TODO["title"]

def test_complete_todo():
    """Test marking a todo as completed."""
    # Create a todo first
    create_response = client.post("/todos/", json=TEST_TODO)
    todo_id = create_response.json()["id"]
    
    response = client.put(f"/todos/{todo_id}/complete")
    assert response.status_code == 200
    assert "marked as completed" in response.json()["message"]
    
    # Verify it's completed
    todos_response = client.get("/todos/")
    todo = next(t for t in todos_response.json() if t["id"] == todo_id)
    assert todo["completed"]

def test_uncomplete_todo():
    """Test marking a todo as not completed."""
    # Create a completed todo first
    create_response = client.post("/todos/", json=TEST_TODO)
    todo_id = create_response.json()["id"]
    client.put(f"/todos/{todo_id}/complete")
    
    response = client.put(f"/todos/{todo_id}/uncomplete")
    assert response.status_code == 200
    assert "marked as not completed" in response.json()["message"]
    
    # Verify it's not completed
    todos_response = client.get("/todos/")
    todo = next(t for t in todos_response.json() if t["id"] == todo_id)
    assert not todo["completed"]

def test_delete_todo():
    """Test deleting a todo."""
    # Create a todo first
    create_response = client.post("/todos/", json=TEST_TODO)
    todo_id = create_response.json()["id"]
    
    response = client.delete(f"/todos/{todo_id}")
    assert response.status_code == 200
    assert "deleted" in response.json()["message"]
    
    # Verify it's deleted
    todos_response = client.get("/todos/")
    assert not any(t["id"] == todo_id for t in todos_response.json())

def test_search_todos():
    """Test searching todos."""
    # Create some todos
    client.post("/todos/", json={"title": "Buy milk", "description": "Get 2% milk"})
    client.post("/todos/", json={"title": "Do laundry"})
    client.post("/todos/", json={"title": "Buy bread", "description": "Get milk bread"})
    
    # Search for 'milk' - should find todos with 'milk' in title or description
    response = client.get("/todos/search", params={"query": "milk"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3  # Should find all todos containing 'milk'
    
    # Verify the correct todos are found
    titles = {todo["title"] for todo in data}
    assert "Buy milk" in titles
    assert "Buy bread" in titles  # Has 'milk' in description
    
    # Search for a non-existent term
    response = client.get("/todos/search", params={"query": "nonexistent"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0

@patch('code_generator.CodeGenerator.save_code')
def test_generate_code(mock_save_code):
    """Test code generation endpoint."""
    # Mock save_code to return True
    mock_save_code.return_value = True
    
    response = client.post("/generate-code/", json=TEST_CODE_REQUEST)
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == TEST_CODE_REQUEST["language"]
    assert data["description"] == TEST_CODE_REQUEST["description"]
    assert "file_path" in data
    assert "content" in data
    assert "created_at" in data

def test_invalid_todo():
    """Test creating a todo with invalid data."""
    response = client.post("/todos/", json={})
    assert response.status_code == 422  # Validation error

def test_nonexistent_todo():
    """Test operations on non-existent todo."""
    response = client.put("/todos/999/complete")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_invalid_code_request():
    """Test code generation with invalid request."""
    response = client.post("/generate-code/", json={})
    assert response.status_code == 422  # Validation error

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 