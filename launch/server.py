"""
FastAPI server implementation for AutoCodeRover.
Provides endpoints for todo management and code generation.
"""

import os
import sys
import json
import asyncio
import logging
import subprocess
from typing import List, Optional, Dict, Tuple, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from models import TodoItem
from db_utils import DatabaseManager
from todo_commands import TodoCommands
from code_generator import CodeGenerator, CodeTask, MCPContext, clean_code_document, clean_file_of_triple_quotes, clean_file_of_backticks
import groq
from env_manager import IsolatedEnvironment
from git_manager import GitManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AutoCodeRover API",
    description="API for managing todos and generating code",
    version="1.0.0"
)

# Initialize components
db_manager = DatabaseManager(os.getenv("DB_PATH", "todos.db"))
todo_commands = TodoCommands(db_manager)

# Get Groq API key from environment
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    logger.warning("No GROQ_API_KEY found in environment. Code generation will be disabled.")

# Initialize code generator and git manager
code_generator = CodeGenerator(api_key=api_key, project_dir="project")
git_manager = GitManager(os.path.abspath(os.path.dirname(__file__)))

# Store for patch run results and tasks
patch_run_results: Dict[str, Dict[str, Any]] = {}
patch_tasks: Dict[str, asyncio.Task] = {}

# Git configuration models
class GitConfig(BaseModel):
    name: str
    email: str

class GitRemote(BaseModel):
    name: str
    url: str

class GitCommit(BaseModel):
    message: str
    files: List[str]

class GitPush(BaseModel):
    remote: str = "origin"
    branch: str = "main"

class PatchPush(BaseModel):
    """Model for pushing a patch to git."""
    patch_id: str
    commit_message: Optional[str] = None
    remote: str = "origin"
    branch: str = "main"

# Git endpoints
@app.post("/git/init")
async def init_git():
    """Initialize a new git repository."""
    if git_manager.init():
        return {"message": "Git repository initialized successfully"}
    raise HTTPException(status_code=500, detail="Failed to initialize git repository")

@app.post("/git/config")
async def configure_git(config: GitConfig):
    """Configure git user name and email."""
    if git_manager.configure_user(config.name, config.email):
        return {"message": "Git user configured successfully"}
    raise HTTPException(status_code=500, detail="Failed to configure git user")

@app.post("/git/remote")
async def add_remote(remote: GitRemote):
    """Add a git remote."""
    if git_manager.set_remote(remote.name, remote.url):
        return {"message": f"Remote {remote.name} added successfully"}
    raise HTTPException(status_code=500, detail="Failed to add remote")

@app.post("/git/commit")
async def create_commit(commit: GitCommit):
    """Create a git commit."""
    if not git_manager.add(commit.files):
        raise HTTPException(status_code=500, detail="Failed to add files")
    if git_manager.commit(commit.message):
        return {"message": "Changes committed successfully"}
    raise HTTPException(status_code=500, detail="Failed to commit changes")

@app.post("/git/push")
async def push_changes(push: GitPush):
    """Push changes to remote repository."""
    if git_manager.push(push.remote, push.branch):
        return {"message": f"Changes pushed to {push.remote}/{push.branch} successfully"}
    raise HTTPException(status_code=500, detail="Failed to push changes")

@app.get("/git/status")
async def get_status():
    """Get git repository status."""
    success, status = git_manager.get_status()
    if success:
        return {"status": status}
    raise HTTPException(status_code=500, detail="Failed to get git status")

@app.post("/git/push-patch/{patch_id}")
async def push_patch(patch_id: str, push: PatchPush):
    """Push a specific patch to git repository."""
    try:
        # Construct patch directory path
        patch_dir = os.path.join(code_generator.patches_dir, patch_id)
        if not os.path.exists(patch_dir):
            raise HTTPException(status_code=404, detail=f"Patch {patch_id} not found")

        # Get relative path from git root to patch directory
        git_root = os.path.abspath(os.path.dirname(__file__))
        rel_patch_dir = os.path.relpath(patch_dir, git_root)

        # Add all files in the patch directory
        files_to_add = [
            os.path.join(rel_patch_dir, "src"),
            os.path.join(rel_patch_dir, "requirements.txt"),
            os.path.join(rel_patch_dir, "metadata.txt"),
            os.path.join(rel_patch_dir, "README.md")
        ]

        # Create commit message if not provided
        commit_message = push.commit_message or f"Add patch: {patch_id}"

        # Add and commit files
        if not git_manager.add(files_to_add):
            raise HTTPException(status_code=500, detail="Failed to add patch files to git")

        if not git_manager.commit(commit_message):
            raise HTTPException(status_code=500, detail="Failed to commit patch files")

        # Push to remote
        if not git_manager.push(push.remote, push.branch):
            raise HTTPException(status_code=500, detail="Failed to push patch to remote repository")

        return {
            "message": f"Patch {patch_id} pushed successfully to {push.remote}/{push.branch}",
            "commit_message": commit_message,
            "files": files_to_add
        }

    except Exception as e:
        logger.error(f"Error pushing patch: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_patch_metadata(patch_id: str) -> CodeTask:
    """Get metadata for a patch."""
    try:
        # Get the absolute path to the workspace root
        workspace_root = os.path.dirname(os.path.abspath(__file__))
        
        # Construct patch directory path
        patch_dir = os.path.join(workspace_root, "project", "patches", patch_id)
        if not os.path.exists(patch_dir):
            raise ValueError(f"Patch directory not found: {patch_id}")
        
        # Read metadata file
        metadata_path = os.path.join(patch_dir, "metadata.txt")
        if not os.path.exists(metadata_path):
            # If no metadata file, create a basic task from the patch ID
            description = patch_id.replace("_", " ").strip()
            return CodeTask(
                description=description,
                language="python",
                requirements=[],
                context=None
            )
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            
        return CodeTask(
            description=metadata.get("description", patch_id),
            language=metadata.get("language", "python"),
            requirements=metadata.get("requirements", []),
            context=metadata.get("context")
        )
    except Exception as e:
        logger.error(f"Failed to get patch metadata: {str(e)}")
        # Return a basic task if metadata can't be read
        return CodeTask(
            description=patch_id,
            language="python",
            requirements=[],
            context=None
        )

async def execute_patch(patch_id: str) -> Tuple[bool, str, str, int]:
    """Execute a patch and return its output.
    
    Args:
        patch_id: The ID of the patch to execute
        
    Returns:
        Tuple[bool, str, str, int]: (success, stdout, stderr, return_code)
    """
    try:
        # Get workspace root and patch directory
        workspace_root = os.path.dirname(os.path.abspath(__file__))
        patch_dir = os.path.join(workspace_root, "project", "patches", patch_id)
        src_dir = os.path.join(patch_dir, "src")
        
        # Get list of files
        if not os.path.exists(src_dir):
            raise ValueError("Source directory not found")
        
        files = os.listdir(src_dir)
        if not files:
            raise ValueError("No files found in source directory")
            
        # Clean and execute each Python file
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(src_dir, file)
                
                # Clean the file of both triple quotes and backticks
                clean_file_of_triple_quotes(file_path)
                clean_file_of_backticks(file_path)
                
                # Create isolated environment
                env = IsolatedEnvironment(patch_dir)
                try:
                    # Setup environment
                    if not env.create():
                        return False, "", "Failed to create virtual environment", 1
                    
                    if not env.install_requirements():
                        return False, "", "Failed to install requirements", 1
                    
                    # Execute the file
                    success, stdout, stderr, return_code = env.run_script(file_path)
                    
                    if not success:
                        return False, stdout, stderr, return_code
                        
                finally:
                    # Always cleanup
                    env.cleanup()
                    
        return True, "Patch executed successfully", "", 0
        
    except Exception as e:
        return False, "", str(e), 1

async def run_patch_task(patch_id: str, analyze: bool = True):
    """Run patch and optionally analyze output."""
    try:
        # Update initial status
        patch_run_results[patch_id] = {
            "success": False,
            "output": "Processing...",
            "error_output": "",
            "return_code": 0,
            "analysis": None,
            "suggested_improvements": None,
            "completed": False,
            "was_regenerated": False
        }

        # Get workspace root and patch directory
        workspace_root = os.path.dirname(os.path.abspath(__file__))
        patch_dir = os.path.join(workspace_root, "project", "patches", patch_id)
        src_dir = os.path.join(patch_dir, "src")
        
        # Get list of files
        if not os.path.exists(src_dir):
            raise ValueError("Source directory not found")
        
        files = os.listdir(src_dir)
        if not files:
            raise ValueError("No files found in source directory")
            
        main_file = files[0]  # Get the first Python file

        # Execute the code and capture output
        success, output, error_output, return_code = await execute_patch(patch_id)
        
        # Check for error indicators in both stdout and stderr
        error_indicators = [
            "error processing grades",
            "division by zero",
            "should trigger",
            "invalid",
            "exception",
            "error",
            "failed",
            "traceback"
        ]
        
        # Move error messages from stdout to stderr if they contain error indicators
        if output and any(indicator.lower() in output.lower() for indicator in error_indicators):
            error_output = output if not error_output else f"{error_output}\n{output}"
            output = ""
        
        # Check for errors in either output stream
        has_error = (
            return_code != 0 or
            bool(error_output) or
            any(indicator.lower() in (output + error_output).lower() for indicator in error_indicators)
        )
        
        # Set execution success and prepare for potential regeneration
        execution_success = not has_error
        needs_regeneration = has_error
        
        # Initialize patch run results
        patch_run_results[patch_id] = {
            "success": execution_success,
            "output": output,
            "error_output": error_output,
            "return_code": return_code,
            "analysis": None,  # Will be set later if analyze=True
            "suggested_improvements": None,  # Will be set later if analyze=True
            "completed": False,  # Not done yet
            "was_regenerated": False  # Will be set to True if regeneration happens
        }
        
        # Get patch metadata
        task = None
        try:
            task = await get_patch_metadata(patch_id)
        except Exception as e:
            logger.error(f"Failed to get patch metadata: {str(e)}")
            patch_run_results[patch_id]["completed"] = True
            return
        
        # If we have errors, try to regenerate the code
        if needs_regeneration:
            # Get current code for regeneration
            current_code = ""
            try:
                with open(os.path.join(src_dir, main_file), 'r') as f:
                    current_code = f.read()
            except Exception as e:
                logger.error(f"Failed to read current code: {str(e)}")
                current_code = "# Failed to read current code"
                patch_run_results[patch_id]["completed"] = True
                return
            
            # Create RAG prompt for code improvement
            rag_prompt = f"""The following code failed to execute properly:

Code:
{current_code}

Execution Output:
{output}

Error Output:
{error_output}

Original Requirements:
{task.description}
{', '.join(task.requirements) if task.requirements else 'No specific requirements provided'}

Please generate an improved version that fixes the issues. The code should:
1. Handle all edge cases in the test data:
   - Empty grade lists (avoid division by zero)
   - Invalid grade types (convert or reject)
   - Out of bounds grades (validate range)
   - Invalid student names (validate keys)
   - Missing or None values (proper handling)
2. Add proper input validation
3. Include descriptive error messages
4. Maintain the original interface
5. Add type hints and docstrings
6. Include example usage with test data

CRITICAL: DO NOT include any triple backticks (```) or language tags in your response. Return ONLY the raw Python code."""

            try:
                if not code_generator.client:
                    logger.warning("OpenAI client not available. Skipping code regeneration.")
                    patch_run_results[patch_id]["completed"] = True
                    return
                    
                response = code_generator.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an expert programmer. Generate improved code that fixes execution issues. NEVER use triple backticks or language tags in your response."},
                        {"role": "user", "content": rag_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=2000,
                    response_format={ "type": "text" }
                )

                if response and response.choices:
                    improved_code = response.choices[0].message.content.strip()
                    logger.info(f"Generated code:\n{improved_code}")
                    
                    # Save improved code
                    file_path = os.path.join(src_dir, main_file)
                    with open(file_path, 'w') as f:
                        f.write(improved_code)
                    
                    # Clean the file of backticks
                    clean_file_of_backticks(file_path)
                    
                    # Log the cleaned code
                    with open(file_path, 'r') as f:
                        cleaned_code = f.read()
                    logger.info(f"Cleaned code:\n{cleaned_code}")
                    
                    # Re-run the improved code
                    success, new_output, new_error_output, new_return_code = await execute_patch(patch_id)
                    
                    # Update results with regeneration info
                    execution_success = new_return_code == 0 and not new_error_output
                    output = f"Original execution:\n{output}\n\nAfter code regeneration:\n{new_output}"
                    error_output = f"Original errors:\n{error_output}\n\nAfter code regeneration:\n{new_error_output}"
                    return_code = new_return_code
                    
                    # Update patch run results with regeneration info
                    patch_run_results[patch_id].update({
                        "success": execution_success,
                        "output": output,
                        "error_output": error_output,
                        "return_code": return_code,
                        "was_regenerated": True,
                        "completed": True
                    })
                    
                    return
            except Exception as e:
                logger.error(f"Failed to regenerate code: {str(e)}")
                patch_run_results[patch_id]["completed"] = True
                return

        # If we get here, either no regeneration was needed or it failed
        patch_run_results[patch_id]["completed"] = True

        # Perform analysis if requested
        analysis = None
        suggested_fixes = None
        if analyze and task and code_generator.client:
            try:
                needs_improvement, analysis, suggested_fixes = code_generator.assess_output(output, error_output, task)
            except Exception as e:
                analysis = f"Error analyzing output: {str(e)}"
                suggested_fixes = []
        
        patch_run_results[patch_id] = {
            "success": execution_success,
            "output": output,
            "error_output": error_output,
            "return_code": return_code,
            "analysis": analysis if analyze else None,
            "suggested_improvements": suggested_fixes if analyze else None,
            "completed": True,
            "was_regenerated": not execution_success and task and code_generator.client
        }
        
    except Exception as e:
        patch_run_results[patch_id] = {
            "success": False,
            "output": str(e),
            "completed": True
        }
    finally:
        # Clean up task
        if patch_id in patch_tasks:
            del patch_tasks[patch_id]

def clean_file_of_backticks(file_path: str) -> None:
    """
    Remove triple backticks and language tags from a file's content.
    
    Args:
        file_path: Path to the file to clean.
    """
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Remove triple backticks and language tags
        if content.startswith("```python"):
            content = content[len("```python"):].lstrip()
        elif content.startswith("```"):
            content = content[3:].lstrip()
            
        if content.endswith("```"):
            content = content[:-3].rstrip()
            
        # Remove any remaining backticks
        content = content.replace("```python", "").replace("```", "").strip()
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    except Exception as e:
        logger.error(f"Failed to clean file {file_path}: {str(e)}")

# Pydantic models for request/response validation
class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None

class TodoResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    completed: bool
    created_at: str

class CodeGenerationRequest(BaseModel):
    description: str
    language: str = "python"
    requirements: List[str] = []
    context: Optional[str] = None

class CodeGenerationResponse(BaseModel):
    file_path: str
    content: str
    language: str
    description: str
    created_at: str

class RunPatchRequest(BaseModel):
    patch_id: str
    analyze: bool = True  # Whether to perform GPT analysis

class RunPatchResponse(BaseModel):
    status: str
    message: str
    execution_output: Optional[str] = None
    error_output: Optional[str] = None
    return_code: Optional[int] = None
    analysis: Optional[str] = None
    suggested_improvements: Optional[List[str]] = None
    was_regenerated: Optional[bool] = None  # Whether the code was regenerated due to execution failure

class PatchRunStatus(BaseModel):
    success: bool
    output: str
    error_output: Optional[str] = None
    return_code: Optional[int] = None
    analysis: Optional[str] = None
    suggested_improvements: Optional[List[str]] = None
    completed: bool = False
    was_regenerated: Optional[bool] = None  # Whether the code was regenerated due to execution failure

# Todo endpoints
@app.post("/todos/", response_model=TodoResponse)
async def create_todo(todo: TodoCreate):
    """Create a new todo item."""
    todo_item = TodoItem(
        title=todo.title,
        description=todo.description,
        created_at=datetime.now().isoformat()
    )
    if db_manager.add_todo(todo_item):
        # Get the created todo to return its ID
        todos = db_manager.get_todos()
        created_todo = next((t for t in todos if t.title == todo.title), None)
        if created_todo:
            return TodoResponse(**created_todo.to_dict())
    raise HTTPException(status_code=500, detail="Failed to create todo")

@app.get("/todos/", response_model=List[TodoResponse])
async def list_todos():
    """List all todo items."""
    todos = db_manager.get_todos()
    return [TodoResponse(**todo.to_dict()) for todo in todos]

@app.put("/todos/{todo_id}/complete")
async def complete_todo(todo_id: int):
    """Mark a todo as completed."""
    if todo_commands.complete_todo(todo_id):
        return {"message": f"Todo {todo_id} marked as completed"}
    raise HTTPException(status_code=404, detail="Todo not found")

@app.put("/todos/{todo_id}/uncomplete")
async def uncomplete_todo(todo_id: int):
    """Mark a todo as not completed."""
    if todo_commands.uncomplete_todo(todo_id):
        return {"message": f"Todo {todo_id} marked as not completed"}
    raise HTTPException(status_code=404, detail="Todo not found")

@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: int):
    """Delete a todo item."""
    if todo_commands.delete_todo(todo_id):
        return {"message": f"Todo {todo_id} deleted"}
    raise HTTPException(status_code=404, detail="Todo not found")

@app.get("/todos/search")
async def search_todos(query: str):
    """Search todos by title or description."""
    todos = todo_commands.search_todos(query)
    return [TodoResponse(**todo.to_dict()) for todo in todos]

# Code generation endpoints
@app.post("/generate-code/", response_model=CodeGenerationResponse)
async def generate_code(request: CodeGenerationRequest):
    """Generate code based on description and requirements."""
    try:
        task = CodeTask(
            description=request.description,
            language=request.language,
            requirements=request.requirements,
            context=request.context
        )
        
        generated_code = code_generator.generate_code(task)
        
        if code_generator.save_code(generated_code):
            return CodeGenerationResponse(
                file_path=generated_code.file_path,
                content=generated_code.content,
                language=generated_code.language,
                description=generated_code.description,
                created_at=datetime.now().isoformat()
            )
        raise HTTPException(status_code=500, detail="Failed to save generated code")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run-patch/", response_model=RunPatchResponse)
async def run_patch(request: RunPatchRequest):
    """Run patch code with optional analysis."""
    try:
        # Cancel existing task if any
        if request.patch_id in patch_tasks:
            patch_tasks[request.patch_id].cancel()
            
        # Create and store new task
        task = asyncio.create_task(run_patch_task(request.patch_id, request.analyze))
        patch_tasks[request.patch_id] = task
        
        return RunPatchResponse(
            status="processing",
            message=f"Started processing patch {request.patch_id}. Check /patch-status/{request.patch_id} for updates."
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/execute-patch/", response_model=RunPatchResponse)
async def execute_patch_endpoint(request: RunPatchRequest):
    """Execute patch code directly without analysis - fast execution."""
    try:
        # Run the patch task directly
        await run_patch_task(request.patch_id, request.analyze)
        
        # Get the results
        result = patch_run_results[request.patch_id]
        
        # Check if regeneration was needed
        if result.get("was_regenerated") is None:
            # If was_regenerated is not set, check if there were errors
            has_error = (
                result.get("return_code", 0) != 0 or
                bool(result.get("error_output", "")) or
                any(indicator.lower() in (result.get("output", "") + result.get("error_output", "")).lower() for indicator in [
                    "error processing grades",
                    "division by zero",
                    "should trigger",
                    "invalid",
                    "exception",
                    "error",
                    "failed",
                    "traceback"
                ])
            )
            result["was_regenerated"] = has_error
        
        return RunPatchResponse(
            status="completed",
            message="Execution completed",
            execution_output=result.get("output", ""),
            error_output=result.get("error_output", ""),
            return_code=result.get("return_code", 1),
            analysis=result.get("analysis"),
            suggested_improvements=result.get("suggested_improvements"),
            was_regenerated=result.get("was_regenerated", False)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patch-status/{patch_id}", response_model=PatchRunStatus)
async def get_patch_status(patch_id: str):
    """Get the status of a patch run."""
    if patch_id not in patch_run_results:
        raise HTTPException(status_code=404, detail=f"No status found for patch {patch_id}")
    return PatchRunStatus(**patch_run_results[patch_id])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 