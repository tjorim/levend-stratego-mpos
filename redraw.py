"""Redraw flow: what happens to a badge that loses an encounter (settles #3).

Decided: physical round-trip, not instant reassignment. Losing (or drawing
- engine.BOTH_LOSE counts too, both sides lose) disarms a badge: it holds
no live rank until it physically returns to its team's base and gets in
range of a base beacon, at which point it redraws. This keeps the pacing
the physical paper-card game already has - losing costs you the walk back
- matching the bias the rest of this project already has toward keeping
proximity and movement real (see proximity.py's continuous-broadcast
design) rather than collapsing everything into pure message-passing. The
alternative (instant reassignment) was simpler and more robust against a
base beacon dying or dropping out of range mid-game, but loses that pacing
entirely - accepted as a known limitation instead: run more than one base
beacon per team so a single failed beacon doesn't strand a team, the same
way you wouldn't run a whole camp off one radio anyway. This mirrors how
the Bomb's stationary rule (RULES.md) is already an honor-system limit
this project accepts rather than tries to solve in code.

A base isn't a new wire concept - it just broadcasts the same rank-free
presence beacon radio.py already defines (encode_beacon()), so
proximity.ProximityTracker sees it exactly like a player peer with no
changes to that module needed. What makes something a *base* rather than a
player is purely local: each badge is configured (at kickoff, alongside
#5's rank distribution) with the set of its own team's base session ids/
macs.

Not solved here, left as a known simplification tied to #5 (army
distribution): redraw() draws independently each time rather than tracking
a shared pool of pieces already issued, so in principle (rare with 59
pieces per side) two badges could simultaneously hold the same rank after
redraws - same as could already happen with the initial deal if #5's
answer doesn't track a shared pool either.

Wiring this into radio.RadioAdapter (disarming on a losing on_result,
redrawing once BaseTracker.at_base() is true, and copying the result back
into radio_adapter.rank_level/.generation) is left to the badge's main
loop, not this module - matching how RadioAdapter itself takes
rank_level/generation as plain mutable fields rather than owning their
lifecycle.
"""

import random

from ranks import standard_army


class RedrawState:
    """One badge's own rank + generation + disarmed/armed status.

    rank_level and generation mirror the same-named fields on
    radio.RadioAdapter - a caller copies this class's values back into
    those after each redraw.
    """

    def __init__(self, rank_level, generation=0):
        self.rank_level = rank_level
        self.generation = generation
        self.disarmed = False

    def lose(self):
        """Call when engine.resolve() reports this badge lost (or drew) an
        encounter. Disarms it until redraw() succeeds - while disarmed,
        this badge has no valid rank to reveal.
        """
        self.disarmed = True

    def redraw(self, rng=random):
        """Call once BaseTracker says a base beacon is close.

        No-ops (returns None) if not currently disarmed, so idling near a
        base while still armed doesn't burn a redraw. Otherwise draws a
        fresh rank uniformly from the standard army's 59 pieces (so the
        odds of drawing e.g. a Bomb match the physical game's piece
        counts), bumps generation so reveal.RevealGuard rejects any stale
        reveal still naming the old rank, and re-arms the badge.
        """
        if not self.disarmed:
            return None
        self.rank_level = rng.choice(standard_army())
        self.generation += 1
        self.disarmed = False
        return self.rank_level


class BaseTracker:
    """Detects "close enough to a base to redraw," reusing the same
    closeness signal (proximity.ProximityTracker) as player encounters
    rather than inventing a second one.
    """

    def __init__(self, tracker, base_macs):
        self.tracker = tracker
        self.base_macs = set(base_macs)

    def at_base(self):
        """True if any known base beacon is currently close."""
        return any(
            peer.close
            for mac, peer in self.tracker.peers.items()
            if mac in self.base_macs
        )
