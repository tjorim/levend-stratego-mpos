"""Tests for proximity.ProximityTracker.

Run with `python3 -m pytest test_proximity.py` or `python3 test_proximity.py`.
"""

from proximity import ProximityTracker, CLOSE_DBM, CLOSE_STREAK, GONE_AFTER_TICKS

MAC = "aa:bb:cc:dd:ee:ff"
SESSION = "session-1"


def test_not_close_until_streak_reached():
    t = ProximityTracker()
    for _ in range(CLOSE_STREAK - 1):
        t.seen(MAC, SESSION, CLOSE_DBM)
    assert t.ready_for_encounter() == []
    t.seen(MAC, SESSION, CLOSE_DBM)
    assert len(t.ready_for_encounter()) == 1


def test_one_weak_reading_resets_streak():
    t = ProximityTracker()
    for _ in range(CLOSE_STREAK):
        t.seen(MAC, SESSION, CLOSE_DBM)
    assert t.ready_for_encounter()
    t.seen(MAC, SESSION, CLOSE_DBM - 10)  # one bad reading
    assert t.ready_for_encounter() == []
    for _ in range(CLOSE_STREAK - 1):
        t.seen(MAC, SESSION, CLOSE_DBM)
    assert t.ready_for_encounter() == []
    t.seen(MAC, SESSION, CLOSE_DBM)
    assert t.ready_for_encounter()


def test_mark_encountered_suppresses_retrigger_until_they_separate():
    t = ProximityTracker()
    for _ in range(CLOSE_STREAK):
        t.seen(MAC, SESSION, CLOSE_DBM)
    peer = t.closest_ready()
    assert peer is not None
    t.mark_encountered(peer.mac)
    # still standing close - shouldn't re-trigger every tick
    t.seen(MAC, SESSION, CLOSE_DBM)
    assert t.ready_for_encounter() == []
    # they step apart...
    t.seen(MAC, SESSION, CLOSE_DBM - 10)
    # ...and close the distance again - should be able to trigger a fresh encounter
    for _ in range(CLOSE_STREAK):
        t.seen(MAC, SESSION, CLOSE_DBM)
    assert t.ready_for_encounter()


def test_new_session_resets_streak():
    t = ProximityTracker()
    for _ in range(CLOSE_STREAK):
        t.seen(MAC, SESSION, CLOSE_DBM)
    assert t.ready_for_encounter()
    # same MAC, different session - the peer's badge restarted
    t.seen(MAC, "session-2", CLOSE_DBM)
    assert t.ready_for_encounter() == []


def test_peers_age_out_when_beacons_stop():
    t = ProximityTracker()
    t.seen(MAC, SESSION, CLOSE_DBM)
    assert MAC in t.peers
    for _ in range(GONE_AFTER_TICKS + 1):
        t.tick()
    assert MAC not in t.peers


def test_closest_ready_picks_strongest_signal():
    t = ProximityTracker()
    for _ in range(CLOSE_STREAK):
        t.seen("near", SESSION, CLOSE_DBM)
        t.seen("far", SESSION, CLOSE_DBM - 3)
    assert t.closest_ready().mac == "near"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("all tests passed")
