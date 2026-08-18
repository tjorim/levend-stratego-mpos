"""Tests for radio.py's protocol/state-machine logic (encode/decode and
RadioAdapter), using a simulated transport instead of real ESP-NOW - see
radio.py's module docstring for why the real ESPNowTransport can't be
covered this way.

Run with `python3 -m pytest test_radio.py` or `python3 test_radio.py`.
"""

from proximity import CLOSE_DBM, CLOSE_STREAK
from engine import A_WINS, B_WINS, BOTH_LOSE
from radio import RadioAdapter, encode_beacon, encode_reveal, decode, BEACON, REVEAL

MAC_A = "aa:bb:cc:dd:ee:01"
MAC_B = "aa:bb:cc:dd:ee:02"


class World:
    """Wires two or more RadioAdapters together: a send() from one adapter
    is delivered to on_receive() on every other adapter registered here,
    simulating a shared broadcast medium without any real radio.
    """

    def __init__(self):
        self.adapters = {}  # mac -> adapter

    def add(self, mac, adapter):
        self.adapters[mac] = adapter
        adapter._send = lambda dst, payload, _mac=mac: self._deliver(
            _mac, dst, payload
        )

    def _deliver(self, src_mac, dst_mac, payload):
        for mac, adapter in self.adapters.items():
            if mac == src_mac:
                continue
            if dst_mac not in (src_mac, "ff:ff:ff:ff:ff:ff", mac):
                continue  # unicast to someone else - not delivered here
            adapter.on_receive(src_mac, rssi=CLOSE_DBM, payload=payload)


def close_approach(world):
    """Drive both sides' beacons until they've both crossed CLOSE_STREAK -
    mirrors two badges standing next to each other, each hearing the
    other's presence beacon every interval."""
    for _ in range(CLOSE_STREAK):
        for adapter in world.adapters.values():
            adapter.send_beacon()


def test_encode_decode_roundtrip_beacon():
    payload = encode_beacon(MAC_A, "session-a")
    assert decode(payload) == {"type": BEACON, "mac": MAC_A, "session": "session-a"}


def test_encode_decode_roundtrip_reveal():
    payload = encode_reveal(MAC_A, "session-a", 2, 5, "deadbeef")
    assert decode(payload) == {
        "type": REVEAL,
        "mac": MAC_A,
        "session": "session-a",
        "generation": 2,
        "rank_level": 5,
        "encounter_key": "deadbeef",
    }


def test_decode_rejects_garbage():
    assert decode(b"not one of ours") is None
    assert decode(b"B|only-two-fields") is None
    assert decode(b"R|a|b|not-an-int|5|key") is None


def test_two_close_badges_resolve_and_notify_both_sides():
    world = World()
    a = RadioAdapter(MAC_A, "session-a", rank_level=5, generation=0, send=None)
    b = RadioAdapter(MAC_B, "session-b", rank_level=3, generation=0, send=None)
    world.add(MAC_A, a)
    world.add(MAC_B, b)

    results = {}
    a.on_result = lambda mac, outcome: results.setdefault("a", outcome)
    b.on_result = lambda mac, outcome: results.setdefault("b", outcome)

    close_approach(world)

    # higher level wins: A (5) beats B (3)
    assert results["a"] == A_WINS
    assert results["b"] == B_WINS


def test_equal_ranks_both_lose():
    world = World()
    a = RadioAdapter(MAC_A, "session-a", rank_level=4, generation=0, send=None)
    b = RadioAdapter(MAC_B, "session-b", rank_level=4, generation=0, send=None)
    world.add(MAC_A, a)
    world.add(MAC_B, b)

    results = {}
    a.on_result = lambda mac, outcome: results.setdefault("a", outcome)
    b.on_result = lambda mac, outcome: results.setdefault("b", outcome)

    close_approach(world)

    assert results["a"] == BOTH_LOSE
    assert results["b"] == BOTH_LOSE


def test_resolve_only_fires_once_per_approach():
    world = World()
    a = RadioAdapter(MAC_A, "session-a", rank_level=5, generation=0, send=None)
    b = RadioAdapter(MAC_B, "session-b", rank_level=3, generation=0, send=None)
    world.add(MAC_A, a)
    world.add(MAC_B, b)

    call_count = {"a": 0}
    a.on_result = lambda mac, outcome: call_count.__setitem__("a", call_count["a"] + 1)

    close_approach(world)
    assert call_count["a"] == 1

    # still standing close, beacons keep arriving - must not re-resolve
    for _ in range(5):
        a.send_beacon()
        b.send_beacon()
    assert call_count["a"] == 1


def _separate(world, a, b):
    # a weak reading resets each side's streak (and RadioAdapter's own
    # stale encounter state, per _on_beacon)
    a.on_receive(MAC_B, rssi=CLOSE_DBM - 10, payload=encode_beacon(MAC_B, "session-b"))
    b.on_receive(MAC_A, rssi=CLOSE_DBM - 10, payload=encode_beacon(MAC_A, "session-a"))


def test_reapproaching_without_a_redraw_does_not_re_resolve():
    """Two badges that separate and immediately re-approach without either
    side's rank changing send byte-for-byte the same generation as their
    first encounter - RevealGuard can't tell that apart from a captured
    replay, so it's correctly suppressed rather than resolved again. This
    matches #2's design: only a redraw (a new generation) makes
    re-encountering the same peer meaningful."""
    world = World()
    a = RadioAdapter(MAC_A, "session-a", rank_level=5, generation=0, send=None)
    b = RadioAdapter(MAC_B, "session-b", rank_level=3, generation=0, send=None)
    world.add(MAC_A, a)
    world.add(MAC_B, b)

    call_count = {"a": 0}
    a.on_result = lambda mac, outcome: call_count.__setitem__("a", call_count["a"] + 1)

    close_approach(world)
    assert call_count["a"] == 1

    _separate(world, a, b)
    close_approach(world)
    assert call_count["a"] == 1


def test_reapproaching_after_both_sides_redraw_resolves_again():
    world = World()
    a = RadioAdapter(MAC_A, "session-a", rank_level=5, generation=0, send=None)
    b = RadioAdapter(MAC_B, "session-b", rank_level=3, generation=0, send=None)
    world.add(MAC_A, a)
    world.add(MAC_B, b)

    call_count = {"a": 0, "b": 0}
    a.on_result = lambda mac, outcome: call_count.__setitem__("a", call_count["a"] + 1)
    b.on_result = lambda mac, outcome: call_count.__setitem__("b", call_count["b"] + 1)

    close_approach(world)
    assert call_count == {"a": 1, "b": 1}

    _separate(world, a, b)
    # both badges got a new rank elsewhere (e.g. after losing a different
    # encounter and returning to base, #3) before meeting again
    a.rank_level, a.generation = 2, 1
    b.rank_level, b.generation = 7, 1

    close_approach(world)
    assert call_count == {"a": 2, "b": 2}


def test_replayed_reveal_does_not_resolve_a_second_time():
    world = World()
    a = RadioAdapter(MAC_A, "session-a", rank_level=5, generation=0, send=None)
    b = RadioAdapter(MAC_B, "session-b", rank_level=3, generation=0, send=None)
    world.add(MAC_A, a)
    world.add(MAC_B, b)

    received_by_a = []
    real_on_receive = a.on_receive

    def spy(mac, rssi, payload):
        received_by_a.append(payload)
        real_on_receive(mac, rssi, payload)

    a.on_receive = spy

    call_count = {"a": 0}
    a.on_result = lambda mac, outcome: call_count.__setitem__("a", call_count["a"] + 1)

    close_approach(world)
    assert call_count["a"] == 1

    # replay the reveal B sent to A during the approach - a captured,
    # once-genuinely-valid packet - RevealGuard must reject the duplicate
    # generation rather than resolve a second time
    last_reveal = next(
        payload for payload in reversed(received_by_a) if decode(payload)["type"] == REVEAL
    )
    a.on_receive(MAC_B, CLOSE_DBM, last_reveal)
    assert call_count["a"] == 1


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("all tests passed")
