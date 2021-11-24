"""
vtelem - Test schema loading from files.
"""

# built-in
from pathlib import Path

# internal
from tests.classes import default_object
from tests.resources import get_resource, get_test_schema

# module under test
from vtelem.classes.serdes import SerializableParams
from vtelem.schema import load_schema, load_schema_dir


def test_load_schema():
    """
    Test that simple schema definitions can be instantiated from files and used
    to make a correct validation decision.
    """

    valid = load_schema(get_test_schema("test_valid.yaml"))
    valid_params = SerializableParams(schema=valid)
    obj = default_object(params=valid_params)
    assert obj.valid

    invalid = load_schema(get_test_schema("test_invalid.json"))
    invalid_params = SerializableParams(schema=invalid)
    obj = default_object(params=invalid_params)
    assert not obj.valid


def test_load_schema_dir():
    """Test that we can load schemas from a directory."""

    schemas = load_schema_dir(Path(get_resource("schemas")))
    assert all(x in schemas for x in ["test_valid", "test_invalid"])
