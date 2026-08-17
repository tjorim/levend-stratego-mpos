"""Tests for reveal.encounter_key() and reveal.RevealGuard.

Run with `python3 -m pytest test_reveal.py` if pytest is installed, or just
`python3 test_reveal.py` directly - no dependencies either way.
"""

from reveal import encounter_key, RevealGuard

MAC_A = "aa:bb:cc:dd:ee:01"
MAC_B = "aa:bb:cc:dd:ee:02"
MAC_C = "aa:bb:cc:dd:ee:03"


def test_encounter_key_is_order_independent():
    assert encounter_key("session-a", "session-b") == encounter_key(
        "session-b", "session-a"
    )


def test_encounter_key_differs_per_pairing():
    key_ab = encounter_key("session-a", "session-b")
    key_ac = encounter_key("session-a", "session-c")
    assert key_ab != key_ac


def test_fresh_reveal_is_accepted():
    guard = RevealGuard(my_session="b-session")
    key = encounter_key("b-session", "a-session")
    assert guard.accept(MAC_A, "a-session", generation=0, received_key=key) is True


def test_exact_replay_is_rejected():
    guard = RevealGuard(my_session="b-session")
    key = encounter_key("b-session", "a-session")
    assert guard.accept(MAC_A, "a-session", generation=0, received_key=key) is True
    # same peer, same session, same generation - a captured packet replayed verbatim
    assert guard.accept(MAC_A, "a-session", generation=0, received_key=key) is False


def test_stale_generation_after_peer_redraw_is_rejected():
    guard = RevealGuard(my_session="b-session")
    key = encounter_key("b-session", "a-session")
    assert guard.accept(MAC_A, "a-session", generation=1, received_key=key) is True
    # A lost elsewhere and redrew to generation 2, then this later reveal
    # arrives naming generation 1 again (a replay of A's old reveal, or an
    # out-of-order duplicate) - must not resolve against the now-stale rank
    assert guard.accept(MAC_A, "a-session", generation=1, received_key=key) is False
    # a genuinely newer generation from the same peer/session is fine
    assert guard.accept(MAC_A, "a-session", generation=2, received_key=key) is True


def test_replay_against_third_party_is_rejected():
    # A's reveal was valid for its encounter with B (key computed from A's
    # and B's sessions); C never shared that pairing, so C's own
    # locally-computed key can't match a captured A-vs-B message.
    key_for_b = encounter_key("a-session", "b-session")
    guard_c = RevealGuard(my_session="c-session")
    assert (
        guard_c.accept(MAC_A, "a-session", generation=0, received_key=key_for_b)
        is False
    )


def test_reboot_gets_a_fresh_session_and_is_not_blocked_by_old_generation():
    guard = RevealGuard(my_session="b-session")
    key = encounter_key("b-session", "a-session")
    assert guard.accept(MAC_A, "a-session", generation=5, received_key=key) is True
    # peer A's badge restarts: new session id, generation resets to 0 -
    # this is a different live instance, not a replay, so it's accepted
    key_after_reboot = encounter_key("b-session", "a-session-2")
    assert (
        guard.accept(MAC_A, "a-session-2", generation=0, received_key=key_after_reboot)
        is True
    )


def test_independent_peers_tracked_separately():
    guard = RevealGuard(my_session="b-session")
    key_a = encounter_key("b-session", "a-session")
    key_c = encounter_key("b-session", "c-session")
    assert guard.accept(MAC_A, "a-session", generation=3, received_key=key_a) is True
    # a low generation from a different peer isn't compared against A's state
    assert guard.accept(MAC_C, "c-session", generation=0, received_key=key_c) is True


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("all tests passed")
