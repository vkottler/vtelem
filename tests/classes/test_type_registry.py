"""
vtelem - Test the type-registry class's correctness.
"""

# module under test
from vtelem.classes.type_registry import get_default
from vtelem.enums.primitive import Primitive, get_name


def test_type_registry_basic():
    """Test basic functionality of the default type registrar."""

    registry = get_default()
    assert registry.describe() != ""

    # prove you can't double register
    assert not registry.add(get_name(Primitive.BOOL), Primitive.BOOL)[0]

    assert registry.get_type(0) is not None
    assert registry.get_type(1) is not None
    assert registry.get_id("boolean") is not None
    assert registry.get_id("float") is not None
    assert registry.get_id("double") is not None
