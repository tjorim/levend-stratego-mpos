"""Tests for themes.py (settles #6).

Run with `python3 -m pytest test_themes.py` if pytest is installed, or just
`python3 test_themes.py` directly - no dependencies either way.
"""

from ranks import BOMB, FLAG, FLAG_RANK, RANKS, SPY, MAX_LEVEL
from engine import resolve, A_WINS, B_WINS
from themes import MAFIA_FLAG, MAFIA_RANKS, THEMES, theme_names, validate_theme

MARSHAL = MAX_LEVEL
MINER = next(r["level"] for r in RANKS if r.get("defuses_bomb"))


def test_military_theme_is_ranks_py_unchanged():
    assert THEMES["military"] == (RANKS, FLAG_RANK)


def test_mafia_theme_validates_against_ranks_py():
    validate_theme(MAFIA_RANKS, MAFIA_FLAG)


def test_all_registered_themes_validate():
    for name, (theme_ranks, theme_flag) in THEMES.items():
        validate_theme(theme_ranks, theme_flag), name


def test_mafia_names_are_unique_and_present():
    names = [r["name"] for r in MAFIA_RANKS] + [MAFIA_FLAG["name"]]
    assert len(names) == len(set(names))
    assert all(names)


def test_mafia_theme_same_level_count_as_military():
    assert len(MAFIA_RANKS) == len(RANKS)


def test_validate_theme_rejects_wrong_count():
    broken = [dict(r) for r in MAFIA_RANKS]
    broken[0]["count"] += 1
    try:
        validate_theme(broken, MAFIA_FLAG)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_validate_theme_rejects_missing_special_flag():
    broken = [dict(r) for r in MAFIA_RANKS]
    for r in broken:
        if r.get("defuses_bomb"):
            del r["defuses_bomb"]
    try:
        validate_theme(broken, MAFIA_FLAG)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_validate_theme_rejects_missing_level():
    broken = [r for r in MAFIA_RANKS if r["level"] != 0]
    try:
        validate_theme(broken, MAFIA_FLAG)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_validate_theme_rejects_non_flag_flag_entry():
    try:
        validate_theme(MAFIA_RANKS, {"level": FLAG, "name": "The Stash"})
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_theme_names_lists_registered_themes():
    assert set(theme_names()) == {"military", "mafia"}


def test_engine_resolve_unchanged_under_mafia_theme():
    # engine.resolve() only ever looks at levels, never names - a themed
    # rank list doesn't change any actual encounter outcome.
    assert resolve(SPY, MARSHAL) == A_WINS  # Informant beats the Don
    assert resolve(MARSHAL, SPY) == B_WINS
    assert resolve(MINER, BOMB) == A_WINS  # Bomb Squad defuses the Car Bomb
    assert resolve(BOMB, MINER) == B_WINS
    assert resolve(FLAG, BOMB) == B_WINS  # The Stash still always loses


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("all tests passed")
