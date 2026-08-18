"""Named-rank themes for Levend Stratego (settles #6).

A theme is just a same-shaped `ranks.RANKS`/`FLAG_RANK` swap: identical
levels, counts, and special-case flags (`static`, `beats_highest`,
`defuses_bomb`, `is_flag`), only the `name` field differs. `engine.py`,
`proximity.py`, `radio.py`, `redraw.py`, `flag.py` and `assign.py` all key
off level numbers and flags, never names, so a theme plugs in without
touching any of that code - see `ranks.py`'s module docstring, which this
was designed to keep true.

"Maffiakamp" (the obvious reference for a scouting-camp mafia reskin) turns
out to be undocumented beyond a one-line pitch on Scoutpedia - no published
rank hierarchy to adapt - so `MAFIA_RANKS` below is designed from scratch,
picking mafia-flavored roles that keep each rank's actual game behavior
sensible under its new name:

- The Don (Marshal, top of the ladder) can be brought down by a single
  turncoat - the Informant (Spy) - matching "beats_highest": betrayal from
  within is the one thing that gets past a boss's usual defenses.
- Only the Bomb Squad (Miner) defuses a Car Bomb (Bomb); everyone else who
  runs into one loses outright, Don included.
- Lookout (Scout), Soldier (Sergeant), Enforcer (Lieutenant), Capo
  (Captain), Consigliere (Major) and Underboss (General) fill out the
  family hierarchy in between, ladder position unchanged.
- The Flag becomes The Stash - what a family is ultimately protecting -
  since RULES.md's "a teammate carries it instead of a normal rank" framing
  reads just as naturally as a person guarding the family's stash as it
  does a literal flag.

Art/sound per theme (the issue's "later" half) is still unbuilt - only the
name mapping is settled here.
"""

from ranks import FLAG, FLAG_RANK, RANKS

MAFIA_RANKS = [
    {"level": 0, "name": "Car Bomb", "count": 6, "static": True},
    {"level": 1, "name": "Informant", "count": 2, "beats_highest": True},
    {"level": 2, "name": "Lookout", "count": 10},
    {"level": 3, "name": "Bomb Squad", "count": 6, "defuses_bomb": True},
    {"level": 4, "name": "Soldier", "count": 9},
    {"level": 5, "name": "Enforcer", "count": 8},
    {"level": 6, "name": "Capo", "count": 7},
    {"level": 7, "name": "Consigliere", "count": 6},
    {"level": 8, "name": "Underboss", "count": 4},
    {"level": 9, "name": "Don", "count": 1},
]
MAFIA_FLAG = {"level": FLAG, "name": "The Stash", "is_flag": True}

# "military" just re-exports ranks.py's own list/flag, so every theme
# (including the default one) is reachable the same way, through THEMES.
THEMES = {
    "military": (RANKS, FLAG_RANK),
    "mafia": (MAFIA_RANKS, MAFIA_FLAG),
}

_FLAG_KEYS = {"static", "beats_highest", "defuses_bomb", "is_flag"}


def validate_theme(theme_ranks, theme_flag):
    """Check that a (ranks, flag) pair is the same shape as ranks.RANKS/
    FLAG_RANK - same levels, same counts, same special-case flags - so it's
    safe to swap in without engine.py (or anything built on it) breaking.
    Only `name` is allowed to differ. Raises ValueError on a mismatch,
    naming the level and what didn't match.
    """
    by_level = {r["level"]: r for r in RANKS}
    theme_by_level = {r["level"]: r for r in theme_ranks}

    if len(theme_by_level) != len(theme_ranks):
        raise ValueError("theme ranks contain duplicate levels")

    if theme_by_level.keys() != by_level.keys():
        raise ValueError(
            f"theme levels {sorted(theme_by_level)} don't match "
            f"ranks.RANKS levels {sorted(by_level)}"
        )
    for level, want in by_level.items():
        got = theme_by_level[level]
        if got["count"] != want["count"]:
            raise ValueError(
                f"level {level} ({got['name']!r}): count {got['count']} != "
                f"{want['count']}"
            )
        want_flags = {k: want.get(k, False) for k in _FLAG_KEYS}
        got_flags = {k: got.get(k, False) for k in _FLAG_KEYS}
        if got_flags != want_flags:
            raise ValueError(
                f"level {level} ({got['name']!r}): flags {got_flags} != "
                f"{want_flags}"
            )

    if theme_flag.get("level") != FLAG_RANK["level"]:
        raise ValueError(
            f"theme flag level {theme_flag.get('level')} != "
            f"{FLAG_RANK['level']}"
        )
    if not theme_flag.get("is_flag"):
        raise ValueError("theme flag must set is_flag: True")


def theme_names():
    """Available theme names, for whatever config/UI ends up picking one."""
    return list(THEMES.keys())
