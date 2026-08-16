"""Core encounter-resolution engine for Levend Stratego.

Pure logic, no badge/radio/UI dependency - runs identically under CPython
(for design/testing) and MicroPython (on the badge). Plain string constants
instead of `enum` since MicroPython builds don't reliably ship that module.
"""

from ranks import rank, MAX_LEVEL

A_WINS = "a"
B_WINS = "b"
BOTH_LOSE = "draw"


def resolve(a, b):
    """Resolve an encounter between two rank levels (see ranks.RANKS).

    Returns A_WINS, B_WINS, or BOTH_LOSE, from A's perspective. Symmetric:
    resolve(a, b) and resolve(b, a) always report the same actual outcome
    (just with A/B swapped) - unlike the board game, a live encounter has no
    "attacker" square to trigger a stationary Bomb from, so Bomb's special
    case applies the same regardless of who touched whom first.
    """
    a_r, b_r = rank(a), rank(b)

    if a_r.get("static") and b_r.get("static"):
        return BOTH_LOSE  # two Bombs meeting - shouldn't happen in practice
    if a_r.get("static"):
        return B_WINS if b_r.get("defuses_bomb") else A_WINS
    if b_r.get("static"):
        return A_WINS if a_r.get("defuses_bomb") else B_WINS

    if a == MAX_LEVEL and b_r.get("beats_highest"):
        return B_WINS
    if b == MAX_LEVEL and a_r.get("beats_highest"):
        return A_WINS

    if a == b:
        return BOTH_LOSE
    return A_WINS if a > b else B_WINS
