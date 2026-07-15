"""
CLI plugin for _example module.

Demonstrates CLI auto-registration pattern.
Uncomment decorators when shared.cli is available.
"""

# from shared.cli import CLIPlugin, register_command


class ExamplePlugin:
    """CLI commands for example module."""

    namespace = "example"
    version = "1.0.0"
    description = "Example module commands"

    # @register_command(
    #     name="list",
    #     description="List examples",
    #     params=[
    #         {"name": "status", "type": "choice", "choices": ["active", "all"]},
    #     ]
    # )
    async def list_cmd(self, status: str = "active") -> dict:
        """List examples."""
        return {
            "items": [],
            "count": 0,
            "status_filter": status,
        }

    # @register_command(
    #     name="create",
    #     description="Create an example",
    #     params=[
    #         {"name": "name", "type": "string", "required": True},
    #     ]
    # )
    async def create_cmd(self, name: str) -> dict:
        """Create an example."""
        return {
            "id": "new-id",
            "name": name,
            "message": f"Created example: {name}",
        }


def get_plugin():
    """Factory function for plugin discovery."""
    return ExamplePlugin()
