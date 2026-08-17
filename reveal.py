"""Reveal-exchange freshness: anti-replay for the one-time rank-reveal
message two close peers exchange to resolve an encounter (see
engine.resolve()).

Pure logic, no radio dependency - the actual over-the-air adapter (#1) just
needs to attach encounter_key() to an outbound reveal, and run each inbound
reveal through RevealGuard.accept() before trusting its rank field enough to
call engine.resolve().

Threat model: this is a scout-camp minigame over unencrypted ESP-NOW, not a
system defending against a well-resourced attacker who can spoof MAC
addresses and forge arbitrary packets - there's no shared secret here to
build real authentication on. What this guards against is a captured,
genuinely-once-valid reveal message being *replayed*: against a third party
who was never part of the original encounter, or against the original peer
again after they've already moved on to a new rank. That matches the
concrete scenario in issue #2: a peer that already lost this encounter and
redrew shouldn't be able to have their old reveal replayed to fake a result
elsewhere.

Two building blocks, mirroring foxhunt-recovered's encounter_key:

- encounter_key(session_a, session_b): a value both peers can compute
  independently (each already knows its own session id and learns the
  peer's from its presence beacon, per proximity.py) that identifies this
  specific pairing of *live badge instances*. A reveal captured from one
  pairing carries a key that won't match any other pairing - and a badge
  reboot changes its session id, so a message from before a reboot won't
  match either. This is what stops the "replay against a third party"
  case: the encounter_key baked into a captured A-vs-B reveal only ever
  equals encounter_key(A's session, B's session), not encounter_key(C's
  session, anything).
- rank generation: each badge counts how many times its own rank has been
  (re)assigned, starting at 0 for the rank it was dealt at kickoff. A
  reveal names the sender's current generation. RevealGuard remembers the
  highest generation it has already accepted from each (peer, session) and
  rejects anything at or below that - so a reveal naming a rank the sender
  has since redrawn away from can't be replayed to fake a later result,
  even against the same peer in the same session.

What this module does *not* decide: where the generation counter lives and
who bumps it (that's the redraw flow, settled in `redraw.py` - see #3) or
the actual wire format of the reveal message (issue #1, now unblocked by
this design).
"""

import hashlib


def encounter_key(session_a, session_b):
    """Symmetric key identifying one mutual approach between two live badge
    sessions. Order-independent, so both peers compute the same value
    without a handshake round-trip - each just needs its own session id and
    the peer's (already carried by every presence beacon, per proximity.py).
    """
    a, b = sorted((session_a, session_b))
    return hashlib.sha256((a + "|" + b).encode()).hexdigest()[:16]


class RevealGuard:
    """Per-badge gatekeeper for inbound reveals: decides whether one is
    fresh enough to resolve, or a replay that must be dropped.
    """

    def __init__(self, my_session):
        self.my_session = my_session
        self._last_seen = {}  # mac -> (peer_session, highest accepted generation)

    def accept(self, mac, peer_session, generation, received_key):
        """Validate one inbound reveal from `mac`.

        Returns True if it's fresh and should be resolved, False if it must
        be dropped as a replay. Has a side effect on True (records the
        generation as seen), so call this exactly once per inbound reveal -
        it's a consume, not a peek.
        """
        if received_key != encounter_key(self.my_session, peer_session):
            return False  # not a key for *this* pairing of live sessions

        seen = self._last_seen.get(mac)
        if seen is not None:
            seen_session, seen_generation = seen
            if seen_session == peer_session and generation <= seen_generation:
                return False  # same badge instance, no newer than one we already used

        self._last_seen[mac] = (peer_session, generation)
        return True
