"""
Data models for AutoCodeRover.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class TodoItem:
    """Represents a todo item in the system."""
    title: str
    description: Optional[str] = None
    completed: bool = False
    created_at: Optional[str] = None
    id: Optional[int] = None

    def __post_init__(self):
        """Set default values after initialization."""
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Convert the todo item to a dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'completed': self.completed,
            'created_at': self.created_at
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
            created_at=created_at.isoformat() if created_at else None
        )

# Define other models as necessary