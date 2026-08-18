"""Kickoff rank distribution: how each badge gets its first rank (settles #5).

Decided: no game-master badge/console. Each badge self-assigns its own
kickoff rank locally, independently - not from a shared seed (the issue's
other option), and not handed out over the air by any central authority.

Rationale:

- A game-master badge is a single point of failure this project has
  already rejected once for a related problem: redraw.py deliberately uses
  per-team base beacons rather than one central authority, "the same way
  you wouldn't run a whole camp off one radio anyway." A kickoff-only
  game-master avoids the *ongoing* single point of failure, but still
  means one specific piece of hardware has to work, be present, and be in
  range of every player at the one moment the whole game depends on -
  worse odds than the base-beacon problem redraw.py already solved by
  spreading it out.
- "Self-assign from a shared seed" was the issue's other proposed option,
  raising a real concern: relies on every badge honestly computing its
  draw from the seed rather than picking a favorable rank. But that
  concern turns out to be no sharper than a limitation this project has
  already accepted: reveal.py's docstring is explicit that there is "no
  shared secret to build actual message authentication on" - any badge can
  already claim whatever rank_level it likes in a reveal, regardless of
  how that rank was originally assigned. A shared seed does not introduce
  a new hole; a badge willing to lie about its rank could do so whether it
  drew from a seed, a game-master message, or thin air. Given that, a
  shared seed buys synchronization (everyone's draw is reproducible/
  auditable against the same sequence) at the cost of needing that seed
  distributed to every badge at kickoff by *some* channel - which puts the
  same "who hands this out" question right back on the table.
- So: skip the seed too. Each badge draws its own kickoff rank the exact
  same way redraw.py already draws a post-loss rank - `rng.choice()` over
  `ranks.standard_army()`, independently, using its own local RNG. A badge
  freshly turned on at kickoff and one that just walked back from a loss
  go through the identical code path and the identical
  with-replacement-odds simplification redraw.py already documents and
  accepts (no shared pool tracking already-issued pieces, there or here).
  Nothing needs to be exchanged over the air for this at all.

The flag holder (#4) is the one piece *not* drawn this way: RULES.md is
explicit that the flag holder carries the flag "instead of a normal rank,"
not on top of one, so which player that is has to be a decision made
before this function runs, not an outcome of it. Consistent with how team
membership already works here - redraw.py notes each badge is "configured
(at kickoff...) with the set of its own team's base session ids/macs,"
i.e. locally, by whoever's setting a given badge up for the game, not
negotiated over the air - designating a badge as its team's flag holder is
the same kind of local, human kickoff configuration, not a new mechanism.

On peeking at your own rank before choosing when to reveal it (also raised
in #5): not mitigated, deliberately. A badge's owner can always look at
their own screen, the same way a physical-game player can always peek at
their own card - this project isn't trying to hide a badge's rank from the
one person who's supposed to know it (see proximity.py: what's protected
is *other* people learning your rank before an encounter, not you knowing
your own). Solving "the player might dawdle once they've peeked" would
mean policing player behavior, not badge state, which is exactly the kind
of honor-system limit this project already accepts elsewhere (RULES.md's
Bomb-stationary rule, redraw.py's docstring drawing the same parallel).
"""

import random

from ranks import FLAG, standard_army


def assign_kickoff_rank(is_flag_holder, rng=random):
    """One badge's rank at kickoff.

    `is_flag_holder` is a local kickoff decision made by whoever's setting
    the badge up (see module docstring), not something this function
    figures out - pass True for the one player per team designated to
    carry the flag, which returns ranks.FLAG directly and skips the army
    draw entirely.

    Everyone else draws uniformly from the standard army, identical to
    redraw.RedrawState.redraw()'s mid-game draw.
    """
    if is_flag_holder:
        return FLAG
    return rng.choice(standard_army())
