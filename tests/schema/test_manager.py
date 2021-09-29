"""
vtelem - Test the schema-manager module.
"""

# internal
from pathlib import Path

# built-in
from vtelem.classes.serdes import Serializable
from vtelem.schema.manager import SchemaManager

# internal
from tests.resources import get_test_schema, get_resource


def test_schema_manager_basic():
    """Test simple use cases for the schema manager."""

    manager = SchemaManager()
    manager.add(get_test_schema("test_valid.yaml"))
    manager.load_dir(Path(get_resource("schemas")))
    assert manager["test_valid"] is not None
    assert manager.get(Serializable) is not None
    assert Serializable.schema(manager) is not None
