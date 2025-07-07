# PatchPilot Server

A FastAPI server that integrates todo management with autonomous code generation.

## Features

- RESTful API for todo management (create, read, update, delete)
- Code generation endpoint that creates code based on descriptions
- Docker support for easy deployment
- Persistent storage for todos and generated code

## Prerequisites

- Docker
- OpenAI API key

## Environment Variables

- `OPENAI_KEY`: Your OpenAI API key
- `DB_PATH`: Path to SQLite database (default: /app/data/todos.db)
- `PROJECT_DIR`: Directory for generated code (default: /app/project)

## Quick Start

1. Build the Docker image:
   ```bash
   docker build -t patchpilot .
   ```

2. Run the container:
   ```bash
   docker run -d \
     -p 8000:8000 \
     -e OPENAI_KEY=your_api_key \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/project:/app/project \
     patchpilot
   ```

3. Access the API documentation at http://localhost:8000/docs

## API Endpoints

### Todo Management

- `POST /todos/`: Create a new todo
- `GET /todos/`: List all todos
- `PUT /todos/{todo_id}/complete`: Mark todo as completed
- `PUT /todos/{todo_id}/uncomplete`: Mark todo as not completed
- `DELETE /todos/{todo_id}`: Delete a todo
- `GET /todos/search?query=...`: Search todos

### Code Generation

- `POST /generate-code/`: Generate code based on description

## Example Usage

### Create a Todo

```bash
curl -X POST http://localhost:8000/todos/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Implement login", "description": "Add user authentication"}'
```

### Generate Code

```bash
curl -X POST http://localhost:8000/generate-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Create a login form with validation",
    "language": "python",
    "requirements": ["Use FastAPI", "Include password hashing"],
    "context": "Part of a web application"
  }'
```

## Development

To run the server locally without Docker:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables:
   ```bash
   export OPENAI_KEY=your_api_key
   export DB_PATH=todos.db
   export PROJECT_DIR=project
   ```

3. Run the server:
   ```bash
   python server.py
   ```

## Notes

- The server uses SQLite for todo storage
- Generated code is saved in the project directory
- API documentation is available at the /docs endpoint
- All API responses are in JSON format 