"""
Git operations manager for PatchPilot.
This module handles git repository operations like commit, push, etc.
"""

import os
import subprocess
import logging
from typing import Tuple, Optional, List

logger = logging.getLogger(__name__)

class GitManager:
    def __init__(self, repo_path: str):
        """Initialize GitManager.
        
        Args:
            repo_path: Path to the git repository
        """
        self.repo_path = repo_path
        
    def _run_git_command(self, command: List[str]) -> Tuple[bool, str, str]:
        """Run a git command and return the result.
        
        Args:
            command: List of command parts to run
            
        Returns:
            Tuple[bool, str, str]: (success, stdout, stderr)
        """
        try:
            result = subprocess.run(
                ["git"] + command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout, e.stderr
            
    def init(self) -> bool:
        """Initialize a new git repository."""
        success, _, stderr = self._run_git_command(["init"])
        if not success:
            logger.error(f"Failed to initialize git repository: {stderr}")
        return success
        
    def add(self, files: List[str]) -> bool:
        """Add files to git staging.
        
        Args:
            files: List of files to add
        """
        success, _, stderr = self._run_git_command(["add"] + files)
        if not success:
            logger.error(f"Failed to add files: {stderr}")
        return success
        
    def commit(self, message: str) -> bool:
        """Create a git commit.
        
        Args:
            message: Commit message
        """
        success, _, stderr = self._run_git_command(["commit", "-m", message])
        if not success:
            logger.error(f"Failed to commit: {stderr}")
        return success
        
    def push(self, remote: str = "origin", branch: str = "main") -> bool:
        """Push commits to remote repository.
        
        Args:
            remote: Remote name (default: origin)
            branch: Branch name (default: main)
        """
        success, _, stderr = self._run_git_command(["push", remote, branch])
        if not success:
            logger.error(f"Failed to push: {stderr}")
        return success
        
    def set_remote(self, name: str, url: str) -> bool:
        """Set a git remote.
        
        Args:
            name: Remote name (e.g. origin)
            url: Remote URL
        """
        success, _, stderr = self._run_git_command(["remote", "add", name, url])
        if not success:
            logger.error(f"Failed to set remote: {stderr}")
        return success
        
    def get_status(self) -> Tuple[bool, str]:
        """Get git status.
        
        Returns:
            Tuple[bool, str]: (success, status_output)
        """
        success, stdout, stderr = self._run_git_command(["status"])
        if not success:
            logger.error(f"Failed to get status: {stderr}")
            return False, stderr
        return True, stdout
        
    def configure_user(self, name: str, email: str) -> bool:
        """Configure git user name and email.
        
        Args:
            name: Git user name
            email: Git user email
        """
        success1, _, stderr1 = self._run_git_command(["config", "user.name", name])
        if not success1:
            logger.error(f"Failed to set user name: {stderr1}")
            return False
            
        success2, _, stderr2 = self._run_git_command(["config", "user.email", email])
        if not success2:
            logger.error(f"Failed to set user email: {stderr2}")
            return False
            
        return True 