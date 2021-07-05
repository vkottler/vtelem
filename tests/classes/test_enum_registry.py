"""
vtelem - Test the enum-registry class's correctness.
"""

# built-in
from enum import Enum

# module under test
from vtelem.classes.type_registry import get_default
from vtelem.classes.enum_registry import EnumRegistry
from vtelem.classes.user_enum import UserEnum, from_enum


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


def test_enum_registry_basic():
    """Test basic functionality of enum registration"""

    registry = get_default()

    enum_a = UserEnum("a", {0: "a", 1: "b", 2: "c"})
    assert enum_a.describe() != ""
    assert enum_a.get_str(0) == "a"

    enum_b = UserEnum("b", {0: "a", 1: "b", 2: "c"})
    assert enum_b.describe() != ""
    assert enum_b.get_str(0) == "a"

    enum_c = UserEnum("c", {0: "a", 1: "b", 2: "c"})
    assert enum_c.describe() != ""
    assert enum_c.get_str(0) == "a"

    enum_reg = EnumRegistry([enum_a, enum_b, enum_c])
    assert enum_reg.describe() != ""

    assert enum_reg.export(registry)
    assert enum_reg.export(registry)

    assert enum_reg.add_enum(UserEnum("float", {0: "a", 1: "b", 2: "c"}))[0]
    assert not enum_reg.export(registry)
