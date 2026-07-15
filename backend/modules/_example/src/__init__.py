"""
_example module - Reference implementation.

Copy this module to create new modules.
"""

from .models import ExampleModel
from .services import ExampleService
from .api import example_router

__all__ = [
    "ExampleModel",
    "ExampleService",
    "example_router",
]
