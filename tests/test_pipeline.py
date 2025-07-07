#!/usr/bin/env python3

import logging
from code_gen_pipeline import CodeGenPipeline
import time
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pipeline(description=None, language=None, requirements=None, context=None):
    """Test the code generation pipeline with a todo."""
    pipeline = CodeGenPipeline()
    
    try:
        # Use provided arguments or defaults
        todo = {
            "title": description or "Create String Reverser",
            "description": description or "Create a Python function that reverses a string",
            "language": language or "python",
            "requirements": requirements.split(",") if requirements else ["pytest"],
            "context": context or "Need a utility function that can reverse any input string",
            "metadata": {
                "test_framework": "pytest",
                "coverage_target": "100%"
            }
        }
        
        # Create the todo
        logger.info("Creating todo...")
        created_todo = pipeline.create_todo(
            todo["title"],
            todo["description"],
            todo["language"],
            todo.get("requirements"),
            todo.get("context"),
            todo.get("metadata")
        )
        logger.info(f"Created todo with ID: {created_todo['id']}")
        
        # Generate code
        logger.info("Generating code...")
        gen_result = pipeline.generate_code(created_todo["id"])
        patch_id = gen_result.get("patch_id")
        logger.info(f"Generated code with patch ID: {patch_id}")
        
        if not patch_id:
            raise ValueError("No patch ID returned from code generation")
        
        # Run the patch
        logger.info("Running patch...")
        run_result = pipeline.run_patch(created_todo["id"])
        logger.info(f"Run result: {run_result}")
        
        # Wait for patch completion
        logger.info("Waiting for patch completion...")
        max_attempts = 30  # Maximum number of attempts (60 seconds)
        attempt = 0
        
        while attempt < max_attempts:
            try:
                status = pipeline.get_patch_status(patch_id)
                if status.get("completed"):
                    logger.info("Patch completed!")
                    if status.get("success"):
                        logger.info("Test completed successfully!")
                        logger.info(f"Output: {status.get('output', '')}")
                    else:
                        logger.error(f"Test failed: {status.get('error_output', '')}")
                    break
            except Exception as e:
                logger.warning(f"Error checking status (attempt {attempt + 1}): {str(e)}")
            
            attempt += 1
            time.sleep(2)
        
        if attempt >= max_attempts:
            logger.error("Timeout waiting for patch completion")
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        raise

if __name__ == "__main__":
    # Get arguments from command line
    description = sys.argv[1] if len(sys.argv) > 1 else None
    language = sys.argv[2] if len(sys.argv) > 2 else None
    requirements = sys.argv[3] if len(sys.argv) > 3 else None
    context = sys.argv[4] if len(sys.argv) > 4 else None
    
    test_pipeline(description, language, requirements, context) 