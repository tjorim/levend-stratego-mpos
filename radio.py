"""ESP-NOW radio adapter: wires proximity.ProximityTracker, reveal.RevealGuard,
and engine.resolve() to the over-the-air layer.

Two layers, on purpose:

- Wire format + `RadioAdapter` are pure protocol/state-machine logic, no ESP-NOW
  dependency - transport is injected as a `send(mac, payload)` callable, so the
  whole exchange (beacon in, reveal out, reveal in, resolve) can be driven and
  tested with a fake transport (see test_radio.py) the same way proximity.py
  and reveal.py are tested without real badges.
- `ESPNowTransport` is the actual MicroPython `espnow` binding. This part
  can't be unit tested off-device (no `espnow` module under CPython, and no
  way to simulate real RSSI/air behavior) - see the manual test plan in
  DESIGN.md. Only this class touches `espnow`/`network`.

Wire format (two message types, both single-line pipe-delimited strings -
no json dependency, keeps payloads well under ESP-NOW's ~250 byte limit):

- presence beacon: `B|<mac>|<session>` - deliberately rank-free, see the
  security note in proximity.py/DESIGN.md.
- reveal: `R|<mac>|<session>|<generation>|<rank_level>|<encounter_key>` -
  matches the format DESIGN.md settled in #2 (`reveal.py`).
"""

from engine import resolve
from proximity import ProximityTracker
from reveal import RevealGuard, encounter_key

BEACON = "B"
REVEAL = "R"

# Mac addresses are colon-hex strings everywhere above the transport
# boundary (matching proximity.py/reveal.py's test conventions and every
# dict key in this module) - only ESPNowTransport deals in the raw 6 bytes
# espnow itself wants.
BROADCAST_MAC = "ff:ff:ff:ff:ff:ff"


def mac_to_bytes(mac):
    return bytes(int(part, 16) for part in mac.split(":"))


def mac_to_str(mac_bytes):
    return ":".join("%02x" % b for b in mac_bytes)


def encode_beacon(mac, session):
    return ("|".join((BEACON, mac, session))).encode()


def encode_reveal(mac, session, generation, rank_level, key):
    fields = (REVEAL, mac, session, str(generation), str(rank_level), key)
    return ("|".join(fields)).encode()


def decode(payload):
    """Parse an inbound payload into a dict, or None if it doesn't look like
    one of ours (wrong type tag or wrong field count) - callers should just
    ignore anything that comes back None rather than treat it as an error;
    ESP-NOW has no guarantee every peer on the channel is speaking this
    protocol.
    """
    try:
        fields = payload.decode().split("|")
    except (UnicodeDecodeError, AttributeError):
        return None

    if fields[0] == BEACON and len(fields) == 3:
        _, mac, session = fields
        return {"type": BEACON, "mac": mac, "session": session}

    if fields[0] == REVEAL and len(fields) == 6:
        _, mac, session, generation, rank_level, key = fields
        try:
            generation = int(generation)
            rank_level = int(rank_level)
        except ValueError:
            return None
        return {
            "type": REVEAL,
            "mac": mac,
            "session": session,
            "generation": generation,
            "rank_level": rank_level,
            "encounter_key": key,
        }

    return None


class _Encounter:
    """State for one approach against one peer: has my reveal gone out, has
    the peer's rank arrived, has this approach already been resolved."""

    def __init__(self, mac):
        self.mac = mac
        self.sent = False
        self.peer_rank = None
        self.resolved = False


class RadioAdapter:
    """Ties ProximityTracker + RevealGuard + engine.resolve() to a transport.

    `rank_level` and `generation` are public and mutable rather than fixed at
    construction: they belong to the not-yet-built redraw flow (#3) and rank
    assignment (#5), which update them as the game proceeds. `on_result`, if
    set, is called as `on_result(peer_mac, outcome)` once an encounter
    resolves, with `outcome` being one of engine.A_WINS/B_WINS/BOTH_LOSE from
    *this* badge's perspective (A = self, B = peer) - applying that outcome
    to game state (removing pieces, triggering a redraw, ...) is up to the
    caller, not this module.

    Note on re-encountering the same peer: if two badges separate and
    re-approach without either side's `generation` having changed, the
    second reveal exchange is byte-for-byte identical to the first from
    RevealGuard's point of view, so it's dropped as an indistinguishable-
    from-replay duplicate rather than resolved again - by design (#2), not
    a bug here. A meaningful re-encounter with the same peer needs a
    genuine redraw (a bumped `generation`) first.
    """

    def __init__(self, my_mac, my_session, rank_level, generation, send):
        self.my_mac = my_mac
        self.my_session = my_session
        self.rank_level = rank_level
        self.generation = generation
        self._send = send
        self.tracker = ProximityTracker()
        self.guard = RevealGuard(my_session)
        self.on_result = None
        self._encounters = {}

    def send_beacon(self):
        """Call on every beacon interval to broadcast presence."""
        self._send(BROADCAST_MAC, encode_beacon(self.my_mac, self.my_session))

    def tick(self):
        """Call once per beacon interval, alongside send_beacon()."""
        self.tracker.tick()

    def on_receive(self, mac, rssi, payload):
        """Feed one inbound ESP-NOW packet (any type) in. `mac` is the
        address the transport actually delivered the packet from; `rssi` is
        only meaningful for beacons. Dropped if the payload's own embedded
        mac field doesn't match - a mismatch means either a malformed/
        spoofed message or a badge relaying someone else's packet, neither
        of which this protocol supports.
        """
        msg = decode(payload)
        if msg is None or msg["mac"] != mac:
            return
        if msg["type"] == BEACON:
            self._on_beacon(mac, rssi, msg)
        elif msg["type"] == REVEAL:
            self._on_reveal(mac, msg)

    def _on_beacon(self, mac, rssi, msg):
        peer = self.tracker.seen(mac, msg["session"], rssi)
        if peer.streak == 0:
            # stepped apart (or a fresh/rebooted session) - drop any past
            # encounter so a future approach starts clean rather than being
            # blocked by a stale "already sent"/"already resolved" state
            self._encounters.pop(mac, None)
        self._maybe_start_reveal()

    def _maybe_start_reveal(self):
        peer = self.tracker.closest_ready()
        if peer is None:
            return
        self.tracker.mark_encountered(peer.mac)
        enc = self._encounters.setdefault(peer.mac, _Encounter(peer.mac))
        if not enc.sent:
            key = encounter_key(self.my_session, peer.session)
            self._send(
                peer.mac,
                encode_reveal(
                    self.my_mac, self.my_session, self.generation, self.rank_level, key
                ),
            )
            enc.sent = True
        self._maybe_resolve(enc)

    def _on_reveal(self, mac, msg):
        if not self.guard.accept(
            mac, msg["session"], msg["generation"], msg["encounter_key"]
        ):
            return
        enc = self._encounters.setdefault(mac, _Encounter(mac))
        enc.peer_rank = msg["rank_level"]
        self._maybe_resolve(enc)

    def _maybe_resolve(self, enc):
        if enc.resolved or enc.peer_rank is None or not enc.sent:
            return
        enc.resolved = True
        outcome = resolve(self.rank_level, enc.peer_rank)
        if self.on_result:
            self.on_result(enc.mac, outcome)


class ESPNowTransport:
    """Real MicroPython ESP-NOW binding for RadioAdapter. Untestable off-
    device - see the manual test plan in DESIGN.md. Kept deliberately thin:
    all protocol logic lives in RadioAdapter above, this class only turns
    espnow's send/recv into the (mac, rssi, payload) shape RadioAdapter
    expects, and tracks add_peer() calls (ESP-NOW requires a peer be added
    before sending to it, broadcast included).
    """

    def __init__(self):
        import network
        import espnow

        sta = network.WLAN(network.STA_IF)
        sta.active(True)
        self._e = espnow.ESPNow()
        self._e.active(True)
        self._known_peers = set()
        self._add_peer(mac_to_bytes(BROADCAST_MAC))

    def _add_peer(self, mac_bytes):
        if mac_bytes not in self._known_peers:
            self._e.add_peer(mac_bytes)
            self._known_peers.add(mac_bytes)

    def send(self, mac, payload):
        mac_bytes = mac_to_bytes(mac)
        self._add_peer(mac_bytes)
        self._e.send(mac_bytes, payload)

    def poll(self, timeout_ms=0):
        """Non-blocking-by-default receive: returns (mac, rssi, payload) or
        (None, None, None) if nothing arrived within timeout_ms.
        """
        mac_bytes, payload = self._e.recv(timeout_ms)
        if mac_bytes is None:
            return None, None, None
        return mac_to_str(mac_bytes), self._peer_rssi(mac_bytes), payload

    def _peer_rssi(self, mac_bytes):
        # peers_table is a MicroPython ESPNow extension: mac -> [rssi,
        # time_ms, ...]. Falls back to 0 if unavailable on a given port/
        # firmware build - closeness detection then degrades until this is
        # confirmed on real hardware (see manual test plan).
        table = getattr(self._e, "peers_table", None)
        if table and mac_bytes in table:
            return table[mac_bytes][0]
        return 0
