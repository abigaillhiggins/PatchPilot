"""
Model Context Protocol (MCP) client for AutoCodeRover.
This module handles communication with an MCP server to provide context-aware code generation.
"""

import os
import json
import logging
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class MCPContext:
    """Represents context information from MCP server."""
    workspace_root: str
    current_file: Optional[str] = None
    open_files: List[str] = None
    cursor_position: Optional[Dict[str, int]] = None
    git_context: Optional[Dict[str, Any]] = None
    language_context: Optional[Dict[str, Any]] = None
    project_context: Optional[Dict[str, Any]] = None

class MCPClient:
    """Client for interacting with MCP server."""
    
    def __init__(self, server_url: str, api_key: Optional[str] = None):
        """Initialize MCP client.
        
        Args:
            server_url: URL of the MCP server
            api_key: Optional API key for authentication
        """
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key or os.getenv('MCP_API_KEY')
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({'Authorization': f'Bearer {self.api_key}'})

    def get_context(self, workspace_path: str) -> MCPContext:
        """Get context information from MCP server.
        
        Args:
            workspace_path: Path to the workspace root
            
        Returns:
            MCPContext object containing context information
        """
        try:
            response = self.session.get(
                f"{self.server_url}/context",
                params={'workspace': workspace_path}
            )
            response.raise_for_status()
            data = response.json()
            
            return MCPContext(
                workspace_root=workspace_path,
                current_file=data.get('current_file'),
                open_files=data.get('open_files', []),
                cursor_position=data.get('cursor_position'),
                git_context=data.get('git_context'),
                language_context=data.get('language_context'),
                project_context=data.get('project_context')
            )
        except Exception as e:
            logger.error(f"Error getting context from MCP server: {e}")
            # Return basic context if server fails
            return MCPContext(workspace_root=workspace_path)

    def update_context(self, context: MCPContext) -> bool:
        """Update context information on MCP server.
        
        Args:
            context: MCPContext object with updated information
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            response = self.session.post(
                f"{self.server_url}/context",
                json={
                    'workspace_root': context.workspace_root,
                    'current_file': context.current_file,
                    'open_files': context.open_files,
                    'cursor_position': context.cursor_position,
                    'git_context': context.git_context,
                    'language_context': context.language_context,
                    'project_context': context.project_context
                }
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error updating context on MCP server: {e}")
            return False

    def get_file_content(self, file_path: str, start_line: int = None, end_line: int = None) -> Optional[str]:
        """Get file content from MCP server.
        
        Args:
            file_path: Path to the file
            start_line: Optional start line number (1-based)
            end_line: Optional end line number (1-based)
            
        Returns:
            str: File content or None if error
        """
        try:
            params = {'path': file_path}
            if start_line is not None:
                params['start_line'] = start_line
            if end_line is not None:
                params['end_line'] = end_line
                
            response = self.session.get(
                f"{self.server_url}/file",
                params=params
            )
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Error getting file content from MCP server: {e}")
            return None

    def get_git_info(self, workspace_path: str) -> Optional[Dict[str, Any]]:
        """Get Git information from MCP server.
        
        Args:
            workspace_path: Path to the workspace root
            
        Returns:
            dict: Git information or None if error
        """
        try:
            response = self.session.get(
                f"{self.server_url}/git",
                params={'workspace': workspace_path}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting Git info from MCP server: {e}")
            return None

    def get_language_info(self, file_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get language information from MCP server.
        
        Args:
            file_path: Optional path to a specific file
            
        Returns:
            dict: Language information or None if error
        """
        try:
            params = {}
            if file_path:
                params['path'] = file_path
                
            response = self.session.get(
                f"{self.server_url}/language",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting language info from MCP server: {e}")
            return None

    def get_project_info(self, workspace_path: str) -> Optional[Dict[str, Any]]:
        """Get project information from MCP server.
        
        Args:
            workspace_path: Path to the workspace root
            
        Returns:
            dict: Project information or None if error
        """
        try:
            response = self.session.get(
                f"{self.server_url}/project",
                params={'workspace': workspace_path}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting project info from MCP server: {e}")
            return None 