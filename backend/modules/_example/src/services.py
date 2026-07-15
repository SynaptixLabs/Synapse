"""
Business logic for _example module.

Replace with your actual services.
"""

import uuid
from typing import List, Optional

from .models import ExampleModel


class ExampleService:
    """Example service with business logic."""

    def __init__(self):
        # In real implementation: inject dependencies
        self._items: dict[str, ExampleModel] = {}

    async def list_items(self, status: Optional[str] = None) -> List[ExampleModel]:
        """List all items, optionally filtered by status."""
        items = list(self._items.values())
        if status:
            items = [i for i in items if i.status == status]
        return items

    async def get_item(self, item_id: str) -> Optional[ExampleModel]:
        """Get a single item by ID."""
        return self._items.get(item_id)

    async def create_item(self, name: str) -> ExampleModel:
        """Create a new item."""
        item = ExampleModel(
            id=str(uuid.uuid4()),
            name=name,
        )
        self._items[item.id] = item
        return item

    async def delete_item(self, item_id: str) -> bool:
        """Delete an item by ID."""
        if item_id in self._items:
            del self._items[item_id]
            return True
        return False
