#!/usr/bin/env python3
"""
Main entry point for PatchPilot.
This script provides a unified interface to run different components of the system.
"""

import os
import sys
import argparse
import logging

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.main import AutoDatabaseManager
from api.server import app
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description='PatchPilot - Code Generation and Management System')
    parser.add_argument('mode', choices=['server', 'cli'], help='Run mode: server (API) or cli (command line)')
    parser.add_argument('--port', type=int, default=8000, help='Port number for server mode')
    parser.add_argument('--host', default='0.0.0.0', help='Host for server mode')
    parser.add_argument('--command', help='Command to run in CLI mode')
    parser.add_argument('--args', nargs=argparse.REMAINDER, help='Arguments for CLI command')
    return parser.parse_args()

def main():
    args = parse_args()
    
    try:
        if args.mode == 'server':
            logger.info(f"Starting server on {args.host}:{args.port}")
            uvicorn.run(app, host=args.host, port=args.port)
        
        elif args.mode == 'cli':
            if not args.command:
                logger.error("Command required in CLI mode")
                sys.exit(1)
                
            # Initialize the database manager
            db_path = os.getenv('DB_PATH', 'todos.db')
            auto_manager = AutoDatabaseManager(db_path)
            
            # Process CLI commands
            if args.command == 'generate-code':
                description = args.args[0] if args.args else None
                language = args.args[1] if len(args.args) > 1 else 'python'
                requirements = args.args[2:] if len(args.args) > 2 else []
                
                if not description:
                    logger.error("Code description required")
                    sys.exit(1)
                    
                if auto_manager.generate_code(description, language, requirements):
                    logger.info("Code generated successfully!")
                else:
                    logger.error("Failed to generate code")
                    sys.exit(1)
            
            else:
                logger.error(f"Unknown command: {args.command}")
                sys.exit(1)
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 