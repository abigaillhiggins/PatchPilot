# PatchPilot Workflows and Commands

This document describes the various workflows and commands available in PatchPilot.

## Table of Contents
- [Todo Management](#todo-management)
- [Code Generation](#code-generation)
- [Combined Workflows](#combined-workflows)
- [Search and Filter](#search-and-filter)
- [Patch Management](#patch-management)

## Todo Management

### Create a Todo
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"title": "Task name", "description": "Task details"}' \
  http://localhost:8000/todos/
```

### List All Todos
```bash
curl http://localhost:8000/todos/
```

### Mark Todo as Completed
```bash
curl -X PUT http://localhost:8000/todos/{todo_id}/complete
```

### Mark Todo as Not Completed
```bash
curl -X PUT http://localhost:8000/todos/{todo_id}/uncomplete
```

### Delete a Todo
```bash
curl -X DELETE http://localhost:8000/todos/{todo_id}
```

## Code Generation

### Generate Code Directly
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "description": "Description of the code to generate",
    "language": "python",
    "requirements": ["Requirement 1", "Requirement 2"],
    "context": "Additional context"
  }' \
  http://localhost:8000/generate-code/
```

### Code Generation via Todo
1. Create a todo with code generation description:
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "title": "Generate code",
    "description": "Detailed description of the code to generate"
  }' \
  http://localhost:8000/todos/
```

2. Use todo description to generate code:
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "description": "Copy description from todo",
    "language": "python",
    "requirements": ["Requirements based on todo"],
    "context": "From todo item #{todo_id}"
  }' \
  http://localhost:8000/generate-code/
```

3. Mark todo as completed:
```bash
curl -X PUT http://localhost:8000/todos/{todo_id}/complete
```

## Combined Workflows

### Code Generation Project Management
1. Create multiple todos for different parts of a project:
```bash
# Create main feature todo
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "title": "Create calculator class",
    "description": "Implement a calculator class with basic operations"
  }' \
  http://localhost:8000/todos/

# Create test todo
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "title": "Write calculator tests",
    "description": "Create unit tests for calculator class"
  }' \
  http://localhost:8000/todos/
```

2. Generate code for each todo
3. Mark todos as completed as you progress

### Feature Development Workflow
1. Create feature planning todos
2. Generate initial code structure
3. Create implementation todos
4. Generate implementation code
5. Create test todos
6. Generate test code
7. Mark todos complete as you progress

## Search and Filter

### Search Todos
```bash
curl "http://localhost:8000/todos/search?query=your_search_term"
```

### Search by Status
Use the search endpoint with specific terms:
```bash
# Search for completed items
curl "http://localhost:8000/todos/search?query=completed"

# Search for specific types of tasks
curl "http://localhost:8000/todos/search?query=generate"
```

## Patch Management

### Run a Generated Patch
```bash
# Run a specific patch by its directory name
curl -X POST -H "Content-Type: application/json" \
  -d '{"patch_id": "20250702_065415_create_a_python_data_validation_utility"}' \
  http://localhost:8000/run-patch/
```

### Command Line Usage
```bash
# Run a patch using the CLI
python main.py run-patch 20250702_065415_create_a_math_utility
```

The run-patch command will:
1. Find the specified patch directory
2. Read the metadata to determine language and requirements
3. Install any required dependencies (for Python patches)
4. Execute the main source file
5. Analyze the execution output
6. Automatically improve the code if needed
7. Repeat steps 4-6 up to 3 times or until the code works correctly

The system uses GPT-4 to:
1. Analyze execution output for:
   - Error messages or exceptions
   - Incorrect output format or content
   - Performance issues
   - Missing functionality
   - Best practices violations

2. Generate specific improvements when issues are found
3. Update the code with fixes
4. Document changes in metadata.txt

Currently supported languages:
- Python (.py files)
- JavaScript/TypeScript (.js/.ts files)

Tips for Running Patches:
1. Make sure all dependencies are available in requirements.txt
2. Check the metadata.txt file for language and requirements
3. Ensure the patch directory has a src/ folder with the main code file
4. Review the README.md for any special instructions
5. Check metadata.txt for improvement history and analysis

Example Workflow:
1. Generate code:
```bash
python main.py generate-code "Create a math utility" --language python
```

2. Find the generated patch ID:
```bash
ls project/patches/
```

3. Run the patch with automatic improvement:
```bash
python main.py run-patch 20250702_065415_create_a_math_utility
```

4. Review improvements in metadata.txt:
```bash
cat project/patches/20250702_065415_create_a_math_utility/metadata.txt
```

Best Practices:
1. Always check the patch requirements before running
2. Use a virtual environment to isolate dependencies
3. Review the generated code before running
4. Monitor the improvement process in the logs
5. Check metadata.txt for improvement history
6. Keep patches organized and documented

Understanding Improvement Logs:
- The system will show:
  1. Original execution output
  2. Analysis of any issues
  3. Specific improvements being made
  4. New execution output after fixes
  5. Final success/failure status

Example improvement log:
```
Running patch 20250702_065415_create_a_math_utility...
Output:
Error: division by zero in factorial calculation

Analysis:
- Missing input validation for negative numbers
- No error handling for edge cases
- Inefficient implementation of factorial

Improvements:
1. Adding input validation
2. Implementing error handling
3. Optimizing factorial calculation

Running improved code...
Output:
All tests passed. Factorial(5) = 120

Patch execution successful!
```

The improvement process will:
1. Stop if the code works correctly
2. Try up to 3 improvement attempts
3. Document all changes in metadata.txt
4. Preserve the original code in git history

If you need to skip automatic improvements:
- Not yet implemented, but you can modify the code manually after each run

## Example Workflows

### 1. Create a New Feature
```bash
# 1. Create planning todo
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "title": "Plan user authentication",
    "description": "Design user authentication system with login/logout"
  }' \
  http://localhost:8000/todos/

# 2. Create implementation todos
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "title": "Implement login function",
    "description": "Create login function with password hashing"
  }' \
  http://localhost:8000/todos/

# 3. Generate code
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "description": "Create login function with password hashing",
    "language": "python",
    "requirements": ["Use bcrypt for hashing", "Return JWT token"],
    "context": "User authentication system"
  }' \
  http://localhost:8000/generate-code/
```

### 2. Bug Fix Workflow
```bash
# 1. Create bug tracking todo
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "title": "Fix division by zero",
    "description": "Add error handling for division by zero in calculator"
  }' \
  http://localhost:8000/todos/

# 2. Generate fix
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "description": "Add error handling for division by zero",
    "language": "python",
    "requirements": ["Raise custom exception", "Add error message"],
    "context": "Calculator class bug fix"
  }' \
  http://localhost:8000/generate-code/
```

## Best Practices

1. **Descriptive Todos**: Make todo descriptions as detailed as possible for better code generation.
2. **Incremental Development**: Break down large features into smaller todos.
3. **Context Awareness**: Always provide context in code generation requests.
4. **Test Integration**: Create separate todos for tests when generating new features.
5. **Status Tracking**: Keep todos updated as you progress through development.

## Tips

- Use the search functionality to group related todos
- Include error handling requirements in code generation descriptions
- Add test requirements in the code generation context
- Keep track of generated file paths for future reference
- Use todo descriptions to document design decisions 