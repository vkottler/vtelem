"""
vtelem - Test the Serializable class's correctness.
"""

# module under test
from vtelem.classes.serdes import Serializable


def test_serializable_basic():
    """
    Test that a serializable object can be decoded and then encoded while
    remaining equal to the original object.
    """

    assert Serializable()
    data = {"a": 1, "b": 2, "c": 3}
    obj = Serializable(data)
    new_obj = obj.load_str(obj.json_str())
    assert obj == new_obj
