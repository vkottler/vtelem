
"""
vtelem - Test the program's entry-point.
"""

# third-party
import netifaces  # type: ignore

# module under test
from vtelem import PKG_NAME
from vtelem.entry import main as vt_main


def test_entry():
    """ Test some basic command-line argument scenarios. """

    assert vt_main([PKG_NAME, "-u", "1"]) == 0
    assert vt_main([PKG_NAME, "-u", "1", "-i", netifaces.interfaces()[0]]) == 0
    assert vt_main([PKG_NAME, "bad_arg"]) != 0
