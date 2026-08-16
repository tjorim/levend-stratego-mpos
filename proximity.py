"""Proximity detection: turns a stream of (peer, rssi) readings into a
"these two are close enough to trigger an encounter" signal.

Deliberately pure/testable, no ESP-NOW dependency - the actual over-the-air
adapter (not written yet) just needs to call seen()/tick() with whatever it
receives and read ready_for_encounter() to know when to kick off a rank
reveal via engine.resolve().

Security note: this layer only ever sees a MAC and a session id, never a
rank. Unlike foxhunt-recovered's snuffel_link.py - which broadcasts a
player's full creature roster in every presence beacon - the beacon feeding
this module must stay rank-free. Broadcasting rank continuously would let a
passive listener always know who's weak/strong before ever making contact,
defeating the whole point of a secret rank. Rank only gets exchanged in a
direct, one-time reveal once ready_for_encounter() says two peers are close.
"""

CLOSE_DBM = -55
CLOSE_STREAK = 4
GONE_AFTER_TICKS = 6


class Peer:
    def __init__(self, mac, session):
        self.mac = mac
        self.session = session
        self.rssi = None
        self.streak = 0
        self.age = 0
        self.encountered = False  # already triggered for this close approach

    @property
    def close(self):
        return self.streak >= CLOSE_STREAK


class ProximityTracker:
    def __init__(self):
        self.peers = {}

    def seen(self, mac, session, rssi):
        """Record one beacon reading from a peer. Call on every received beacon."""
        peer = self.peers.get(mac)
        if peer is None or peer.session != session:
            # new peer, or same MAC but a fresh session (the other badge
            # restarted) - start its streak over rather than carry over
            # closeness earned by whatever was running before
            peer = Peer(mac, session)
            self.peers[mac] = peer
        peer.age = 0
        peer.rssi = rssi
        if rssi >= CLOSE_DBM:
            peer.streak += 1
        else:
            peer.streak = 0
            peer.encountered = False  # left range - a future approach can trigger again
        return peer

    def tick(self):
        """Call once per beacon interval to age out peers we've stopped hearing from."""
        gone = []
        for mac, peer in self.peers.items():
            peer.age += 1
            if peer.age > GONE_AFTER_TICKS:
                gone.append(mac)
        for mac in gone:
            del self.peers[mac]

    def ready_for_encounter(self):
        """Peers that are close and haven't already triggered a reveal this approach."""
        return [p for p in self.peers.values() if p.close and not p.encountered]

    def closest_ready(self):
        """The single best candidate to resolve next, or None. Real encounters are
        1:1 even if several peers happen to be in range at once."""
        ready = self.ready_for_encounter()
        if not ready:
            return None
        return max(ready, key=lambda p: p.rssi)

    def mark_encountered(self, mac):
        """Call once a reveal has actually been triggered against this peer, so
        we don't re-trigger every tick while they're still standing close."""
        peer = self.peers.get(mac)
        if peer is not None:
            peer.encountered = True
