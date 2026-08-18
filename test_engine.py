"""Tests for engine.resolve() against the documented physical rules.

Run with `python3 -m pytest test_engine.py` if pytest is installed, or just
`python3 test_engine.py` directly - no dependencies either way.
"""

from ranks import BOMB, SPY, FLAG, MAX_LEVEL, RANKS, standard_army
from engine import resolve, A_WINS, B_WINS, BOTH_LOSE

MARSHAL = MAX_LEVEL
MINER = next(r["level"] for r in RANKS if r.get("defuses_bomb"))


def test_higher_rank_wins():
    assert resolve(MINER + 1, MINER) == A_WINS
    assert resolve(MINER, MINER + 1) == B_WINS


def test_equal_ranks_both_lose():
    assert resolve(4, 4) == BOTH_LOSE


def test_spy_beats_marshal_only():
    assert resolve(SPY, MARSHAL) == A_WINS
    assert resolve(MARSHAL, SPY) == B_WINS
    # Spy loses to everything else, same as its raw (lowest, non-Bomb) level would suggest
    assert resolve(SPY, MINER) == B_WINS
    assert resolve(MINER, SPY) == A_WINS


def test_bomb_beats_everyone_except_miner():
    for r in RANKS:
        if r["level"] in (BOMB, MINER):
            continue
        assert resolve(BOMB, r["level"]) == A_WINS, r["name"]
        assert resolve(r["level"], BOMB) == B_WINS, r["name"]


def test_miner_defuses_bomb():
    assert resolve(MINER, BOMB) == A_WINS
    assert resolve(BOMB, MINER) == B_WINS


def test_standard_army_size_and_composition():
    army = standard_army()
    assert len(army) == 59  # 6+2+10+6+9+8+7+6+4+1, per the physical game
    assert army.count(MARSHAL) == 1
    assert army.count(SPY) == 2
    assert army.count(BOMB) == 6


def test_flag_always_loses_to_any_rank():
    for r in RANKS:
        assert resolve(FLAG, r["level"]) == B_WINS, r["name"]
        assert resolve(r["level"], FLAG) == A_WINS, r["name"]


def test_flag_loses_to_bomb_too():
    assert resolve(FLAG, BOMB) == B_WINS
    assert resolve(BOMB, FLAG) == A_WINS


def test_two_flags_meeting_both_lose():
    assert resolve(FLAG, FLAG) == BOTH_LOSE


def test_flag_excluded_from_standard_army():
    assert FLAG not in standard_army()


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("all tests passed")
