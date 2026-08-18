"""Tests for assign.assign_kickoff_rank().

Run with `python3 -m pytest test_assign.py` or `python3 test_assign.py`.
"""

import random

from assign import assign_kickoff_rank
from ranks import FLAG, RANKS


class _FixedRng:
    """Stub for assign_kickoff_rank()'s rng param: always "draws" the same
    level, so tests can check what gets passed through without depending on
    actual randomness."""

    def __init__(self, level):
        self.level = level

    def choice(self, seq):
        return self.level


def test_flag_holder_gets_flag_regardless_of_rng():
    assert assign_kickoff_rank(is_flag_holder=True, rng=_FixedRng(9)) == FLAG


def test_flag_holder_does_not_touch_the_army_draw():
    # rng that would blow up if choice() were ever called on it, proving
    # the flag holder path skips the draw rather than drawing-then-
    # discarding it.
    class _ExplodingRng:
        def choice(self, seq):
            raise AssertionError("flag holder should not draw from the army")

    assert assign_kickoff_rank(is_flag_holder=True, rng=_ExplodingRng()) == FLAG


def test_non_flag_holder_draws_the_fixed_level():
    assert assign_kickoff_rank(is_flag_holder=False, rng=_FixedRng(4)) == 4


def test_non_flag_holder_draws_from_the_standard_army_levels():
    levels = {r["level"] for r in RANKS}
    rng = random.Random(42)
    for _ in range(200):
        assert assign_kickoff_rank(is_flag_holder=False, rng=rng) in levels


def test_non_flag_holder_never_draws_flag():
    rng = random.Random(7)
    for _ in range(200):
        assert assign_kickoff_rank(is_flag_holder=False, rng=rng) != FLAG


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("all tests passed")
