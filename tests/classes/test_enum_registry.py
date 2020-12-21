
"""
vtelem - Test the enum-registry class's correctness.
"""

# module under test
from vtelem.classes.type_registry import get_default
from vtelem.classes.enum_registry import EnumRegistry
from vtelem.classes.user_enum import UserEnum


def test_enum_registry_basic():
    """ Test basic functionality of enum registration """

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
