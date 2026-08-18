"""Theme-neutral rank hierarchy for a badge-mediated Levend Stratego.

Ranks are pure data: a level (higher wins on contact) plus a small set of
special-case flags. A theme is just a name (and later, art/sound) mapped onto
this same structure - swap RANKS for a re-themed list and everything else
(engine.py, army composition) keeps working unchanged.

Levels and counts below match the standard physical game as documented on
scouting reference sites (Scoutpedia, Scout's Choice, Scouting Nederland's
activiteitenbank) - see DESIGN.md for sources and the exact rules this was
checked against.
"""

BOMB = 0
SPY = 1

RANKS = [
    {"level": 0, "name": "Bomb", "count": 6, "static": True},
    {"level": 1, "name": "Spy", "count": 2, "beats_highest": True},
    {"level": 2, "name": "Scout", "count": 10},
    {"level": 3, "name": "Miner", "count": 6, "defuses_bomb": True},
    {"level": 4, "name": "Sergeant", "count": 9},
    {"level": 5, "name": "Lieutenant", "count": 8},
    {"level": 6, "name": "Captain", "count": 7},
    {"level": 7, "name": "Major", "count": 6},
    {"level": 8, "name": "General", "count": 4},
    {"level": 9, "name": "Marshal", "count": 1},
]

# The Flag (settles #4): kept out of RANKS/standard_army() on purpose - it's
# a single designated piece assigned once per team at kickoff (tied to #5),
# never part of the shuffled 59-piece draw pool and never redrawn. See
# flag.py for what "is_flag" means to the encounter engine.
FLAG = -1
FLAG_RANK = {"level": FLAG, "name": "Flag", "is_flag": True}

MAX_LEVEL = max(r["level"] for r in RANKS)

_BY_LEVEL = {r["level"]: r for r in RANKS}
_BY_LEVEL[FLAG] = FLAG_RANK


def rank(level):
    """Look up a rank's data by its level."""
    return _BY_LEVEL[level]


def standard_army():
    """One player's full army as a flat list of levels, per the physical game's
    piece counts (59 pieces total: 6+2+10+6+9+8+7+6+4+1 - one Marshal, two
    Spies, six Bombs, etc). Order is unshuffled; callers should shuffle before
    handing pieces out.
    """
    army = []
    for r in RANKS:
        army.extend([r["level"]] * r["count"])
    return army
