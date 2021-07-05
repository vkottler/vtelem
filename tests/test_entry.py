"""
vtelem - Test the program's entry-point.
"""

# built-in
from multiprocessing import Process
import os
import signal
import time

# third-party
import netifaces  # type: ignore

# module under test
from vtelem import PKG_NAME
from vtelem.entry import main as vt_main


def test_entry():
    """Test some basic command-line argument scenarios."""

    assert vt_main([PKG_NAME, "-u", "1"]) == 0
    assert vt_main([PKG_NAME, "-u", "1", "-i", netifaces.interfaces()[0]]) == 0
    assert vt_main([PKG_NAME, "bad_arg"]) != 0


def test_entry_sigint():
    """Test that the program handles keyboard interrupts gracefully."""

    proc = Process(target=vt_main, args=[PKG_NAME, "-u", "10"])
    proc.start()
    time.sleep(1.0)
    os.kill(proc.pid, signal.SIGINT)
    proc.join()
