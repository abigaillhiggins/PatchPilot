"""
Data models for PatchPilot.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime

class TodoItem:
    """Represents a todo item with code generation metadata."""
    
    def __init__(self, title: str, description: Optional[str] = None,
                 completed: bool = False, created_at: Optional[str] = None,
                 language: Optional[str] = None, requirements: Optional[List[str]] = None,
                 package_requirements: Optional[List[str]] = None,
                 context: Optional[str] = None, metadata: Optional[Dict] = None,
                 patch_id: Optional[str] = None, id: Optional[int] = None):
        """Initialize a todo item."""
        self.id = id
        self.title = title
        self.description = description
        self.completed = completed
        self.created_at = created_at or datetime.now().isoformat()
        self.language = language
        self.requirements = requirements or []
        self.package_requirements = package_requirements or []
        self.context = context
        self.metadata = metadata or {}
        self.patch_id = patch_id

    def to_dict(self) -> Dict:
        """Convert todo item to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "completed": self.completed,
            "created_at": self.created_at,
            "language": self.language,
            "requirements": self.requirements,
            "package_requirements": self.package_requirements,
            "context": self.context,
            "metadata": self.metadata,
            "patch_id": self.patch_id
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'TodoItem':
        """Create todo item from dictionary."""
        return cls(
            title=data["title"],
            description=data.get("description"),
            completed=data.get("completed", False),
            created_at=data.get("created_at"),
            language=data.get("language"),
            requirements=data.get("requirements", []),
            package_requirements=data.get("package_requirements", []),
            context=data.get("context"),
            metadata=data.get("metadata", {}),
            patch_id=data.get("patch_id"),
            id=data.get("id")
        )

# Define other models as necessary