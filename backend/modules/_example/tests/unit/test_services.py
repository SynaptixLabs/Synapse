"""
Unit tests for the _example module's ExampleService.

A WORKING reference test — copy its shape for your own modules. Unlike a placeholder, every case
asserts real behavior, so a green run actually proves something. That is Commandment B1 in
practice: no gate closes on assertion, and an assertion-free `pass` test is not evidence.
"""

import sys
from pathlib import Path

import pytest

# Make this module's `src` package importable no matter where pytest is invoked from.
_MODULE_ROOT = Path(__file__).resolve().parents[2]  # .../backend/modules/_example
if str(_MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(_MODULE_ROOT))

from src.models import ExampleModel  # noqa: E402  (path set up above)
from src.services import ExampleService  # noqa: E402


@pytest.fixture
def service() -> ExampleService:
    """A fresh, empty service per test."""
    return ExampleService()


class TestExampleService:
    """Behavioral tests for ExampleService — real assertions, not placeholders."""

    @pytest.mark.asyncio
    async def test_list_items_empty_returns_empty_list(self, service):
        """A brand-new service holds no items."""
        assert await service.list_items() == []

    @pytest.mark.asyncio
    async def test_create_item_valid_returns_model(self, service):
        """Creating an item returns a populated ExampleModel."""
        item = await service.create_item(name="Test Item")

        assert isinstance(item, ExampleModel)
        assert item.name == "Test Item"
        assert item.status == "active"
        assert item.id  # a non-empty generated id

    @pytest.mark.asyncio
    async def test_get_item_exists_returns_item(self, service):
        """An existing item can be fetched by id."""
        created = await service.create_item(name="Test")
        fetched = await service.get_item(created.id)

        assert fetched is not None
        assert fetched.id == created.id

    @pytest.mark.asyncio
    async def test_get_item_not_exists_returns_none(self, service):
        """Fetching an unknown id returns None."""
        assert await service.get_item("nonexistent-id") is None

    @pytest.mark.asyncio
    async def test_list_items_filters_by_status(self, service):
        """The status filter only returns matching items."""
        await service.create_item(name="A")

        assert len(await service.list_items(status="active")) == 1
        assert await service.list_items(status="archived") == []

    @pytest.mark.asyncio
    async def test_delete_item_exists_returns_true(self, service):
        """Deleting an existing item returns True and removes it."""
        created = await service.create_item(name="Test")

        assert await service.delete_item(created.id) is True
        assert await service.get_item(created.id) is None

    @pytest.mark.asyncio
    async def test_delete_item_not_exists_returns_false(self, service):
        """Deleting an unknown id returns False."""
        assert await service.delete_item("nonexistent-id") is False
