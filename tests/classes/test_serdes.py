"""
vtelem - Test the Serializable class's correctness.
"""

# third-party
from cerberus import Validator

# module under test
from vtelem.classes.serdes import Serializable, SerializableParams

# internal
from tests.classes import KEYS, default_object


def test_serializable_basic():
    """
    Test that a serializable object can be decoded and then encoded while
    remaining equal to the original object.
    """

    assert Serializable()

    obj = default_object()
    new_obj = obj.load_str(obj.json_str())
    assert obj == new_obj

    schema = {}
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
