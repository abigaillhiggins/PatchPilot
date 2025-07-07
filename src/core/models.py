"""
Data models for PatchPilot.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime

@dataclass
class TodoItem:
    """Represents a todo item in the system."""
    title: str
    description: Optional[str] = None
    completed: bool = False
    created_at: Optional[str] = None
    id: Optional[int] = None
    language: Optional[str] = None
    requirements: Optional[List[str]] = None
    context: Optional[str] = None
    metadata: Optional[Dict] = None
    patch_id: Optional[str] = None

    def __post_init__(self):
        """Set default values after initialization."""
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.requirements is None:
            self.requirements = []
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> dict:
        """Convert the todo item to a dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'completed': self.completed,
            'created_at': self.created_at,
            'language': self.language,
            'requirements': self.requirements,
            'context': self.context,
            'metadata': self.metadata,
            'patch_id': self.patch_id
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TodoItem':
        """Create a TodoItem instance from a dictionary."""
        created_at = None
        if data.get('created_at'):
            try:
                created_at = datetime.fromisoformat(data['created_at'])
            except (ValueError, TypeError):
                pass

        return cls(
            id=data.get('id'),
            title=data['title'],
            description=data.get('description'),
            completed=data.get('completed', False),
            created_at=created_at.isoformat() if created_at else None,
            language=data.get('language'),
            requirements=data.get('requirements', []),
            context=data.get('context'),
            metadata=data.get('metadata', {}),
            patch_id=data.get('patch_id')
        )

# Define other models as necessary