"""
vtelem - Test the enum-registry class's correctness.
"""

# built-in
from enum import Enum

# internal
from tests.classes.test_serdes import is_serializable

# module under test
from vtelem.classes.user_enum import from_enum, user_enum
from vtelem.registry.enums import EnumRegistry
from vtelem.registry.type import get_default


def test_from_enum():
    """Test that an enum can be constructed from an existing class."""

    class EnumA(Enum):
        """Sample enumeration."""

        A = 0
        B = 1
        C = 2

    enum_a = from_enum(EnumA)
    assert enum_a.get_value("a") == 0
    assert enum_a.get_value("b") == 1
    assert enum_a.get_value("c") == 2
    assert enum_a.get_str(0) == "a"
    assert enum_a.get_str(1) == "b"
    assert enum_a.get_str(2) == "c"

    # make sure we can register this enum
    registry = EnumRegistry()
    assert registry.add_from_enum(EnumA)[0]


def test_enum_serdes():
    """Verify that an enum can be serialized."""

    enum = is_serializable(user_enum("a", {0: "a", 1: "b", 2: "c"}))
    assert all(isinstance(key, int) for key in enum.data["mappings"])


def test_enum_registry_basic():
    """Test basic functionality of enum registration"""

    registry = get_default()

    enum_a = user_enum("a", {0: "a", 1: "b", 2: "c"})
    assert enum_a.get_str(0) == "a"

    enum_b = user_enum("b", {0: "a", 1: "b", 2: "c"})
    assert enum_b.get_str(0) == "a"

    enum_c = user_enum("c", {0: "a", 1: "b", 2: "c"})
    assert enum_c.get_str(0) == "a"

    enum_reg = EnumRegistry([enum_a, enum_b, enum_c])
    assert enum_reg.describe() != ""

    assert enum_reg.export(registry)
    assert enum_reg.export(registry)

    assert enum_reg.add_enum(user_enum("float", {0: "a", 1: "b", 2: "c"}))[0]
    assert not enum_reg.export(registry)
