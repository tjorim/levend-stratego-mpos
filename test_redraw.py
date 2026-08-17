"""Tests for redraw.RedrawState and redraw.BaseTracker.

Run with `python3 -m pytest test_redraw.py` or `python3 test_redraw.py`.
"""

from proximity import ProximityTracker, CLOSE_DBM, CLOSE_STREAK
from ranks import RANKS
from redraw import RedrawState, BaseTracker

BASE_MAC = "aa:bb:cc:dd:ee:01"
PLAYER_MAC = "aa:bb:cc:dd:ee:02"
SESSION = "session-1"


class _FixedRng:
    """Stub for redraw()'s rng param: always "draws" the same level."""

    def __init__(self, level):
        self.level = level

    def choice(self, seq):
        return self.level


def test_armed_badge_is_not_disarmed():
    state = RedrawState(rank_level=4)
    assert state.disarmed is False


def test_losing_disarms():
    state = RedrawState(rank_level=4)
    state.lose()
    assert state.disarmed is True


def test_redraw_noop_while_armed():
    state = RedrawState(rank_level=4, generation=0)
    assert state.redraw(rng=_FixedRng(9)) is None
    assert state.rank_level == 4
    assert state.generation == 0


def test_redraw_after_losing_bumps_generation_and_rearms():
    state = RedrawState(rank_level=4, generation=0)
    state.lose()
    new_level = state.redraw(rng=_FixedRng(9))
    assert new_level == 9
    assert state.rank_level == 9
    assert state.generation == 1
    assert state.disarmed is False


def test_second_redraw_without_losing_again_is_a_noop():
    state = RedrawState(rank_level=4, generation=0)
    state.lose()
    state.redraw(rng=_FixedRng(9))
    assert state.redraw(rng=_FixedRng(0)) is None
    assert state.rank_level == 9
    assert state.generation == 1


def test_redraw_draws_from_the_standard_army_levels():
    state = RedrawState(rank_level=4)
    state.lose()
    new_level = state.redraw(rng=__import__("random").Random(42))
    assert new_level in {r["level"] for r in RANKS}


def test_at_base_false_when_no_base_nearby():
    tracker = ProximityTracker()
    for _ in range(CLOSE_STREAK):
        tracker.seen(PLAYER_MAC, SESSION, CLOSE_DBM)
    bases = BaseTracker(tracker, base_macs=[BASE_MAC])
    assert bases.at_base() is False


def test_at_base_true_once_a_known_base_beacon_is_close():
    tracker = ProximityTracker()
    bases = BaseTracker(tracker, base_macs=[BASE_MAC])
    for _ in range(CLOSE_STREAK - 1):
        tracker.seen(BASE_MAC, SESSION, CLOSE_DBM)
    assert bases.at_base() is False
    tracker.seen(BASE_MAC, SESSION, CLOSE_DBM)
    assert bases.at_base() is True


def test_at_base_ignores_peers_that_are_not_registered_bases():
    tracker = ProximityTracker()
    for _ in range(CLOSE_STREAK):
        tracker.seen(PLAYER_MAC, SESSION, CLOSE_DBM)
    bases = BaseTracker(tracker, base_macs=[BASE_MAC])
    assert bases.at_base() is False


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("all tests passed")
