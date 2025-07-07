#!/usr/bin/env python3
"""
Command-line interface for code generation with patches support.
"""

import os
import sys
import argparse
import json
from code_generator import CodeGenerator, CodeTask

def parse_args():
    parser = argparse.ArgumentParser(description='Generate code and save to patches directory')
    parser.add_argument('--description', '-d', required=True,
                       help='Description of the code to generate')
    parser.add_argument('--language', '-l', default='python',
                       help='Programming language (default: python)')
    parser.add_argument('--requirements', '-r', nargs='+',
                       help='List of requirements (one or more)')
    parser.add_argument('--context', '-c',
                       help='Additional context for code generation')
    parser.add_argument('--output-dir', '-o', default='generated_code',
                       help='Output directory (default: generated_code)')
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_KEY")
    if not api_key:
        print("Error: OPENAI_KEY environment variable not set")
        sys.exit(1)
    
    # Create task from arguments
    task = CodeTask(
        description=args.description,
        language=args.language,
        requirements=args.requirements or [],
        context=args.context
    )
    
    # Initialize code generator
    generator = CodeGenerator(api_key, args.output_dir)
    
    try:
        print(f"\nGenerating code for: {task.description}")
        print(f"Language: {task.language}")
        print(f"Requirements:")
        for req in task.requirements:
            print(f"  - {req}")
        if task.context:
            print(f"Context: {task.context}")
        print("\nGenerating...")
        
        # Generate code
        generated_code = generator.generate_code(task)
        
        # Print results
        patch_dir = os.path.dirname(generated_code.file_path)
        print(f"\nCode generated successfully!")
        print(f"\nFiles generated in: {patch_dir}")
        print("\nGenerated files:")
        for file in os.listdir(patch_dir):
            file_path = os.path.join(patch_dir, file)
            size = os.path.getsize(file_path)
            print(f"  - {file} ({size} bytes)")
            
        # Print metadata
        metadata_path = os.path.join(patch_dir, "metadata.txt")
        if os.path.exists(metadata_path):
            print("\nMetadata:")
            with open(metadata_path, 'r') as f:
                print(f.read())
        
    except Exception as e:
        print(f"Error generating code: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 