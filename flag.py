"""Flag capture: the game's win condition (settles #4).

Decided: a badge-carried flag holder, folded into the existing rank +
encounter machinery (ranks.py, engine.py, reveal.py, radio.py) rather than
a separate wire concept, a fixed base-beacon location, or leaving the flag
physical/analog. Rationale:

- The physical game's flag is a hidden object one team must find - a
  designated player carrying a badge that holds `ranks.FLAG` instead of a
  normal army rank is the closest digital match, and "find and tag" is
  already exactly what the existing proximity-then-reveal flow
  (`proximity.py` + `radio.py`) does for ordinary encounters. No new wire
  message, no new proximity signal.
- A fixed base-beacon location was considered and rejected: it would
  conflate "the flag" with `redraw.py`'s base concept (a team's redraw
  point), and it drops the "carried, must be tracked down" character the
  physical game has - a stationary point is armed-guard-a-location, not
  find-a-person.
- Leaving the flag physical/analog was rejected too: the game needs an
  actual digital win condition (this issue exists specifically because
  nothing currently ends the game), and every other camp-facing mechanic
  is already digitized.
- Kept secret the same way rank is: the flag holder's badge sends the
  exact same rank-free presence beacon as anyone else (`radio.encode_beacon`),
  so there's no way to spot the flag holder from a distance - it only
  reveals as `FLAG` in the same one-time reveal exchange an ordinary
  encounter already triggers.
- `engine.resolve()` makes a Flag always lose, Bomb included (see there) -
  any attacker who reaches it captures it. Unlike an ordinary loss, a
  captured flag holder does not get redrawn (`redraw.py`): the game is
  over for that side. That distinction lives here rather than in
  `engine.py` or `radio.py`, matching how those modules already leave
  game-flow interpretation of an encounter outcome to their callers.

Not solved here, left to #5 (army/rank distribution) and the badge's main
loop, same split `radio.py`/`redraw.py` already use: which player is
designated flag holder at kickoff, and what happens once a capture is
recognised (announcing a winner, ending the game, ...).
"""

from engine import A_WINS, B_WINS, BOTH_LOSE
from ranks import FLAG


def captured_sides(my_rank, peer_rank, outcome):
    """Given one resolved encounter (same (my_rank, peer_rank, outcome)
    shape as engine.resolve()'s inputs/output, from "my" perspective),
    return which side(s), if any, just had their flag captured: a set
    containing "self", "peer", both, or neither.

    engine.resolve() guarantees a Flag always loses, so ordinarily this is
    just "the losing side's rank was FLAG" - but BOTH_LOSE is ambiguous
    between an ordinary equal-rank draw and the rare case of two flag
    holders finding each other, so each side is checked directly against
    the outcome that would actually have lost it, rather than inferred
    from outcome alone.
    """
    sides = set()
    if my_rank == FLAG and outcome in (B_WINS, BOTH_LOSE):
        sides.add("self")
    if peer_rank == FLAG and outcome in (A_WINS, BOTH_LOSE):
        sides.add("peer")
    return sides
