"""
vtelem - Test the Serializable class's correctness.
"""

# third-party
from cerberus import Validator

# module under test
from vtelem.classes.serdes import Serializable, SerializableParams

# internal
from tests.classes import KEYS, default_object


def is_serializable(obj: Serializable) -> Serializable:
    """Verify that a serializable can be correctly encoded and decoded."""

    new_obj = obj.load_str(obj.json_str())
    assert obj == new_obj
    return new_obj


def test_serializable_int_keys():
    """
    Test that the method for converting dictionary keys from Strings to
    integers works with more than one path argument.
    """

    obj = Serializable()
    str_keys = {"1": "a", "2": "b", "3": "c"}
    data = {"a": {"b": str_keys}}
    obj.coerce_int_keys(["a", "b"], data)
    assert all(isinstance(x, int) for x in data["a"]["b"])
    assert data["a"]["b"] == {1: "a", 2: "b", 3: "c"}


def test_serializable_basic():
    """
    Test that a serializable object can be decoded and then encoded while
    remaining equal to the original object.
    """

    assert Serializable()

    obj = is_serializable(default_object())

    schema = {"type": {"type": "string"}}
    for key in KEYS:
        schema[key] = {"type": "integer"}

    # Verify that schema validation works.
    params = SerializableParams(schema=Validator(schema))
    obj = Serializable(obj.data, params)
    assert obj.valid

    schema = {}
    for key in KEYS:
        schema[key] = {"type": "string"}
    params = SerializableParams(schema=Validator(schema))
    obj = Serializable(obj.data, params)
    assert not obj.valid
