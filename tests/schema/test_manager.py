"""
vtelem - Test the schema-manager module.
"""

# internal
from pathlib import Path

# internal
from tests.classes.test_serdes import is_serializable
from tests.resources import get_resource, get_test_schema

# built-in
from vtelem.classes.serdes import Serializable
from vtelem.classes.user_enum import user_enum
from vtelem.schema.manager import SchemaManager


def test_user_enum_schema():
    """
    Test that a UserEnum can be loaded with a schema sourced from this package.
    """

    manager = SchemaManager()
    manager.load_package(require_all=True)
    enum = user_enum("test", {0: "a", 1: "b", 2: "c"}, manager=manager)
    assert enum.valid
    new_enum = is_serializable(enum)
    assert new_enum.valid


def test_schema_manager_basic():
    """Test simple use cases for the schema manager."""

    manager = SchemaManager()
    manager.add(get_test_schema("test_valid.yaml"))
    manager.load_dir(Path(get_resource("schemas")))
    assert manager["test_valid"] is not None
    assert manager.get(Serializable) is not None
    assert Serializable.schema(manager) is not None

    assert "UserEnum" in manager.load_package()
