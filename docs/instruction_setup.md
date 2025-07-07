# PatchPilot Server Setup Instructions

## Prerequisites

- Python 3.13+ (Python 3.13.3 recommended)
- pip (latest version)
- Git

## Setup Steps
```

### 1. Set Up Python Virtual Environment

It's important to use a virtual environment to avoid conflicts with other Python projects. The server requires Python 3.13+.

```bash
# Check Python version first
python --version  # Should be 3.13+

# Create and activate virtual environment
cd launch-container
python -m venv venv
source venv/bin/activate  # On Unix/MacOS
# OR
.\venv\Scripts\activate  # On Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Verify Installation

Make sure all dependencies are correctly installed:
```bash
python -c "import fastapi; import uvicorn; import sqlite3; print('All dependencies installed successfully!')"
```

## Running the Server

### Development Mode
```bash
python server.py
```
The server will start on `http://0.0.0.0:8000`

### Production Mode
For production deployment, it's recommended to use the provided Dockerfile:

```bash
docker build -t autocoder-rover -f Dockerfile .
docker run -p 8000:8000 autocoder-rover
```

## Common Issues and Solutions

### 1. Python Version Error
If you see a SyntaxError related to type hints (like `title: str`), it means you're using an older version of Python. Make sure to:
- Install Python 3.13+
- Activate the virtual environment
- Verify Python version with `python --version`

### 2. SQLite Threading Issues
If you encounter SQLite threading issues:
- Make sure only one instance of the server is running
- Check database file permissions
- Verify the database path in configuration

### 3. Port Already in Use
If port 8000 is already in use:
- Kill any existing server processes
- Change the port in the configuration
- Use `lsof -i :8000` to check what's using the port

## Directory Structure

The server expects the following directory structure:
```
launch-container/
├── server.py          # Main server file
├── requirements.txt   # Dependencies
├── db_utils.py       # Database utilities
├── code_generator.py # Code generation logic
├── models.py         # Data models
└── docs/            # Documentation
    ├── commands.md   # API commands
    └── instruction_setup.md  # This file
```

## Environment Variables

The following environment variables can be configured:
- `PORT`: Server port (default: 8000)
- `HOST`: Server host (default: 0.0.0.0)
- `DEBUG`: Debug mode (default: False)

## Testing

Before deploying, run the test suite:
```bash
python -m pytest
```

All tests should pass before deploying to production.

## Health Check

Once the server is running, you can verify it's working by:

1. Checking the server status:
```bash
curl http://localhost:8000/health
```

2. Creating a test todo:
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"title": "Test todo", "description": "Test description"}' \
  http://localhost:8000/todos/
```

## Monitoring

The server logs to stdout by default. You can monitor it using:
```bash
tail -f server.log  # If logging to file is enabled
```

