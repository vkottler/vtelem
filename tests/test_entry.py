
"""
vtelem - Test the program's entry-point.
"""

# module under test
from vtelem import PKG_NAME
from vtelem.entry import main as vt_main


def test_entry():
    """ Test some basic command-line argument scenarios. """

    assert vt_main([PKG_NAME]) == 0
