"""
vtelem - Test the program's entry-point.
"""

# built-in
from multiprocessing import Process
import os
import signal
from subprocess import check_output
from sys import executable
import time

# third-party
import netifaces

# module under test
from vtelem import PKG_NAME
from vtelem.entry import main as vt_main


def test_entry():
    """Test some basic command-line argument scenarios."""

    assert vt_main([PKG_NAME, "-u", "1"]) == 0
    assert vt_main([PKG_NAME, "-u", "1", "-i", netifaces.interfaces()[0]]) == 0
    assert vt_main([PKG_NAME, "bad_arg"]) != 0


def test_package_entry():
    """Test the command-line entry through the 'python -m' invocation."""

    check_output([executable, "-m", PKG_NAME, "-h"])


def test_entry_sigint():
    """Test that the program handles keyboard interrupts gracefully."""

    proc = Process(target=vt_main, args=[PKG_NAME, "-u", "10"])
    proc.start()
    time.sleep(1.0)
    assert proc.pid is not None
    os.kill(proc.pid, signal.SIGINT)
    proc.join()
