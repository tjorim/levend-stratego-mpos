"""Tests for flag.captured_sides().

Run with `python3 -m pytest test_flag.py` or `python3 test_flag.py`.
"""

from engine import A_WINS, B_WINS, BOTH_LOSE, resolve
from ranks import FLAG
from flag import captured_sides


def test_my_flag_captured_by_a_normal_attacker():
    outcome = resolve(FLAG, 4)
    assert outcome == B_WINS
    assert captured_sides(FLAG, 4, outcome) == {"self"}


def test_i_capture_the_peers_flag():
    outcome = resolve(4, FLAG)
    assert outcome == A_WINS
    assert captured_sides(4, FLAG, outcome) == {"peer"}


def test_two_flags_meeting_captures_both():
    outcome = resolve(FLAG, FLAG)
    assert outcome == BOTH_LOSE
    assert captured_sides(FLAG, FLAG, outcome) == {"self", "peer"}


def test_ordinary_equal_rank_draw_is_not_a_capture():
    outcome = resolve(4, 4)
    assert outcome == BOTH_LOSE
    assert captured_sides(4, 4, outcome) == set()


def test_ordinary_encounter_is_not_a_capture():
    outcome = resolve(6, 4)
    assert outcome == A_WINS
    assert captured_sides(6, 4, outcome) == set()
    assert captured_sides(4, 6, resolve(4, 6)) == set()


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("all tests passed")
