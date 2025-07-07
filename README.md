# PatchPilot

PatchPilot is an API-driven code generation and management system that helps you create, manage, and execute code patches.

## Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/abigaillhiggins/PatchPilot.git
cd PatchPilot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r pipeline_requirements.txt
```

4. Set up environment variables:
```bash
export OPENAI_API_KEY="your-api-key"  # Required for code generation
export DB_PATH="todos.db"  # Optional, defaults to todos.db
```

5. Run the server:
```bash
python -m src.api.server
```

The server will start on `http://localhost:8000`

## API Endpoints

### Git Operations

```bash
# Initialize Git Repository
curl -X POST http://localhost:8000/git/init

# Configure Git User
curl -X POST http://localhost:8000/git/config \
  -H "Content-Type: application/json" \
  -d '{"name": "Your Name", "email": "your.email@example.com"}'

# Add Remote
curl -X POST http://localhost:8000/git/remote \
  -H "Content-Type: application/json" \
  -d '{"name": "origin", "url": "https://github.com/username/repo.git"}'

# Create Commit
curl -X POST http://localhost:8000/git/commit \
  -H "Content-Type: application/json" \
  -d '{"message": "Your commit message", "files": ["path/to/file1", "path/to/file2"]}'

# Push Changes
curl -X POST http://localhost:8000/git/push \
  -H "Content-Type: application/json" \
  -d '{"remote": "origin", "branch": "main"}'

# Get Git Status
curl http://localhost:8000/git/status

# Push Specific Patch
curl -X POST http://localhost:8000/git/push-patch/{patch_id} \
  -H "Content-Type: application/json" \
  -d '{"commit_message": "Optional custom message", "remote": "origin", "branch": "main"}'
```

### Todo Management

```bash
# Create Todo
curl -X POST http://localhost:8000/todos/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Task title",
    "description": "Task description",
    "language": "python",
    "requirements": ["package1", "package2"],
    "context": "Additional context",
    "metadata": {"key": "value"}
  }'

# List All Todos
curl http://localhost:8000/todos/

# Complete Todo
curl -X PUT http://localhost:8000/todos/{todo_id}/complete

# Delete Todo
curl -X DELETE http://localhost:8000/todos/{todo_id}

# Search Todos
curl "http://localhost:8000/todos/search?query=your_search_term"
```

### Code Generation and Execution

```bash
# Generate Code for Todo
curl -X POST http://localhost:8000/generate-code/{todo_id}

# Run Patch with Analysis
curl -X POST http://localhost:8000/run-patch/{todo_id}?analyze=true

# Execute Patch Directly
curl -X POST http://localhost:8000/execute-patch/ \
  -H "Content-Type: application/json" \
  -d '{"patch_id": "your_patch_id", "analyze": true}'

# Get Patch Status
curl http://localhost:8000/patch-status/{patch_id}
```

## Response Models

All endpoints return JSON responses. Common response structures include:

- Success responses include a `message` field describing the operation result
- Error responses include a `detail` field describing what went wrong
- Patch execution responses include:
  - `status`: Current status of the execution
  - `execution_output`: Standard output from the execution
  - `error_output`: Standard error output if any
  - `return_code`: Execution return code
  - `analysis`: Optional analysis of the execution (if requested)
  - `suggested_improvements`: Optional suggestions for code improvement 