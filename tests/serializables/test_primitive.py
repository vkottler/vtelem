"""
vtelem - Test the 'vtelem.serializables.primitive' module.
"""

# module under test
from vtelem.schema.manager import SchemaManager
from vtelem.serializables.primitive import get_all


def test_primitive_basic():
    """Test correctness of the serializable primitives."""

    manager = SchemaManager()
    manager.load_package(require_all=True)
    prims = get_all(manager=manager)
    for prim in prims:
        assert prim.valid
