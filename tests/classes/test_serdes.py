"""
vtelem - Test the Serializable class's correctness.
"""

# third-party
from cerberus import Validator

# module under test
from vtelem.classes.serdes import Serializable, SerializableParams


def test_serializable_basic():
    """
    Test that a serializable object can be decoded and then encoded while
    remaining equal to the original object.
    """

    assert Serializable()

    keys = "abc"
    data = {}
    for idx, string in enumerate(keys):
        data[string] = idx + 1

    obj = Serializable(data)
    new_obj = obj.load_str(obj.json_str())
    assert obj == new_obj

    schema = {}
    for key in keys:
        schema[key] = {"type": "integer"}

    # Verify that schema validation works.
    params = SerializableParams(schema=Validator(schema))
    obj = Serializable(data, params)
    assert obj.valid

    schema = {}
    for key in keys:
        schema[key] = {"type": "string"}
    params = SerializableParams(schema=Validator(schema))
    obj = Serializable(data, params)
    assert not obj.valid
