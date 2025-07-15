from code_generator import CodeGenerator, CodeTask
import os

def main():
    # Initialize code generator
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Please set GROQ_API_KEY environment variable")
        return
    
    generator = CodeGenerator(api_key, "real_test_project")
    
    # Create a simple task
    task = CodeTask(
        description="Create a function to calculate factorial",
        language="python",
        requirements=[
            "Function should be recursive",
            "Should handle non-negative integers",
            "Should raise ValueError for negative numbers",
            "Should include type hints and docstring"
        ],
        context="Creating a mathematical utility function"
    )
    
    # Generate code
    print("Generating code...")
    generated_code = generator.generate_code(task)
    
    print(f"\nCode generated successfully!")
    print(f"Check the files in: {os.path.dirname(generated_code.file_path)}")

if __name__ == "__main__":
    main() 