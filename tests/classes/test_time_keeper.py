
"""
vtelem - Test the time keeper's correctness.
"""

# module under test
from vtelem.classes.time_keeper import TimeKeeper
from vtelem.classes.time_entity import TimeEntity


def test_time_keeper_basic():
    """ Test standard time-keeper operation. """

    keeper = TimeKeeper(0.05)
    slave_a = TimeEntity()
    slave_b = TimeEntity()
    slave_c = TimeEntity()
    keeper.add_slave(slave_a)
    keeper.add_slave(slave_b)
    keeper.add_slave(slave_c)
    assert slave_a.get_time() == slave_b.get_time()
    assert slave_b.get_time() == slave_c.get_time()
    assert slave_c.get_time() == slave_c.get_time()
    assert keeper.time() >= slave_a.get_time()
    assert keeper.time() >= slave_b.get_time()
    assert keeper.time() >= slave_c.get_time()
    assert keeper.start()
    keeper.sleep(0.1)
    keeper.scale(2.0)
    keeper.sleep(0.1)
    keeper.scale(0.5)
    keeper.sleep(0.1)
    assert keeper.stop()
