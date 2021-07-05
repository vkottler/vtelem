"""
vtelem - Test the time keeper's correctness.
"""

# built-in
from multiprocessing import Process
import os
import signal
import time

# module under test
from vtelem.classes.daemon_base import DaemonState
from vtelem.classes.time_keeper import TimeKeeper
from vtelem.classes.time_entity import TimeEntity


def test_time_keeper_interrupted():
    """Test that daemons handle interrupts correctly."""

    keeper = TimeKeeper("time", 0.05)
    proc = Process(target=keeper.run_harness)
    proc.start()
    time.sleep(0.2)
    os.kill(proc.pid, signal.SIGINT)
    proc.join()
    assert keeper.get_state() == DaemonState.IDLE


def test_time_keeper_basic():
    """Test standard time-keeper operation."""

    keeper = TimeKeeper("time", 0.05)
    slave_a = TimeEntity()
    slave_b = TimeEntity()
    slave_c = TimeEntity()
    keeper.add_slave(slave_a)
    keeper.add_slave(slave_b)
    keeper.add_slave(slave_c)
    assert slave_a.get_time() == slave_b.get_time()
    assert slave_b.get_time() == slave_c.get_time()
    assert slave_c.get_time() == slave_c.get_time()
    assert keeper.get_time() >= slave_a.get_time()
    assert keeper.get_time() >= slave_b.get_time()
    assert keeper.get_time() >= slave_c.get_time()
    assert keeper.start()
    keeper.sleep(0.1)
    keeper.scale(2.0)
    keeper.sleep(0.1)
    keeper.scale(0.5)
    keeper.sleep(0.1)
    assert keeper.stop()
