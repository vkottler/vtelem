"""
vtelem - Tests for the enum registry module.
"""

# internal
from tests.classes import EnumA

# module under test
from vtelem.classes.user_enum import from_enum
from vtelem.registry.enum_retry import EnumRegistry
from vtelem.schema.manager import SchemaManager


def test_enum_registry_basic():
    """Test basic interaction with an enum registry."""

    reg = EnumRegistry()
    assert reg.name == "EnumRegistry"

    enum_id = reg.add_from_enum(EnumA)
    user_enum = reg.get_enum(enum_id)
    new_enum = from_enum(EnumA)

    assert user_enum == new_enum

    new_reg = reg.load_str(reg.json_str())
    assert new_reg == reg
    assert new_reg.get_enum(enum_id) == user_enum


def test_enum_registry_schema():
    """Test basic interaction with an enum registry, with schemas enforced."""

    manager = SchemaManager()
    manager.load_package(require_all=True, allow_unknown=False)
    assert manager.get(EnumRegistry)
    reg = EnumRegistry(manager=manager)
    assert reg.valid

    # Test that schemas can be added.
    enum_id = reg.add_from_enum(EnumA)
    user_enum = reg.get_enum(enum_id)
    new_enum = from_enum(EnumA)
    assert user_enum == new_enum

    # Test that a new registry is still equivalent.
    new_reg = reg.load_str(reg.json_str())
    assert new_reg == reg
    assert new_reg.valid
