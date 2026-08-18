# Levend Stratego, badge-mediated

A digital-encounter take on [Levend Stratego](https://nl.scoutwiki.org/Levend_Stratego)
(live-action Stratego, popular at Belgian/Dutch scouting camps): badges hold
your secret rank instead of a paper card, and resolve encounters over
ESP-NOW/LoRa instead of "show me your card." Aimed at a future Fri3d Camp
edition, following the same MicroPythonOS pattern as `bomberboy-mpos` and the
recovered `foxhunt-recovered`.

**Scope right now: the core mechanic only.** Rank hierarchy + encounter
resolution, theme-neutral, tested independent of any badge/radio code. Theming
(mafia or otherwise - see below) is explicitly deferred.

## What's implemented (`ranks.py`, `engine.py`, `test_engine.py`)

The rank hierarchy and piece counts, sourced from
[Scoutpedia](https://nl.scoutwiki.org/Levend_Stratego),
[Scout's Choice](https://scoutschoice.nl/activiteit/levend-stratego/), and
[Scouting Nederland's activiteitenbank](https://activiteitenbank.scouting.nl/component/k2/item/111-levend-stratego):

| Level | Rank (physical name) | Count | Special |
|---|---|---|---|
| 0 | Bomb | 6 | Beats everyone except the Miner |
| 1 | Spy | 2 | Beats only the Marshal |
| 2 | Scout | 10 | |
| 3 | Miner | 6 | Only rank that defuses a Bomb |
| 4 | Sergeant | 9 | |
| 5 | Lieutenant | 8 | |
| 6 | Captain | 7 | |
| 7 | Major | 6 | |
| 8 | General | 4 | |
| 9 | Marshal | 1 | Loses to the Spy |

59 pieces per army. `resolve(a, b)` in `engine.py` implements the full
encounter table (higher level wins; Spy vs. Marshal and Bomb vs. Miner are the
only exceptions; equal ranks both lose) and is unit-tested against all of the
above in `test_engine.py`. Ranks are just names attached to level numbers +
a couple of boolean flags (`static`, `beats_highest`, `defuses_bomb`) - a
theme reskins the names (and later, art), the engine doesn't change.

## What's implemented (`proximity.py`, `test_proximity.py`)

**Decided: ESP-NOW, continuous broadcast + RSSI-closeness, not a paired
handshake.** Rationale: close physical proximity is the point (bump into
whoever's near you, not a pre-arranged 1v1), which is a much closer match to
`foxhunt-recovered`'s `snuffel_link.py` pattern (continuous broadcast + a
peer table with RSSI-smoothed "closeness," N consecutive close readings
before triggering) than to `bomberboy-mpos`'s `network_play.py` (an explicit
async-paired handshake between two specific badges that have already agreed
to a match - wrong shape for "anyone I happen to walk past").

`proximity.py`'s `ProximityTracker` implements that: `seen(mac, session,
rssi)` feeds it readings, a streak of `CLOSE_STREAK` consecutive readings at
or above `CLOSE_DBM` marks a peer "close," `closest_ready()` returns the
single best candidate to actually trigger an encounter against (real
encounters are 1:1 even if several people happen to be in range), and
`mark_encountered()` stops it from re-triggering every tick while two people
are still standing next to each other - that resets once they step apart, so
the same two badges can encounter each other again later. `tick()` ages out
peers whose beacons have stopped arriving.

**Deliberately does not carry rank.** This is the one place this project
diverges from `foxhunt-recovered` on purpose rather than by omission:
`snuffel_link.py` broadcasts a player's full creature roster in every
presence beacon, which is fine for Foxhunt (browsing what's tradeable is
supposed to be visible) but wrong here - broadcasting rank continuously
would let a passive listener always know who's weak/strong before anyone
ever makes contact, destroying the "secret until you touch" premise the
whole game depends on. The presence beacon this module expects only ever
carries a MAC and a session id; rank only gets exchanged in a direct,
one-time reveal once `closest_ready()` says two peers are actually close -
that reveal-and-resolve exchange (`engine.resolve()` sits on the other end
of it) is still unbuilt, see below.

## What's implemented (`reveal.py`, `test_reveal.py`)

**Decided (#2): freshness is `encounter_key` + a per-badge rank
generation counter**, following `foxhunt-recovered`'s `encounter_key`
pattern rather than inventing real cryptographic authentication - this is a
scout-camp minigame over unencrypted ESP-NOW, and there's no shared secret
to build actual message authentication on. The goal is narrower: a captured,
once-genuinely-valid reveal message shouldn't be replayable to fake a
result, either against a third party who was never part of the original
encounter, or against the same peer again after they've moved on to a new
rank.

Two pieces, both pure/testable in `reveal.py`:

- `encounter_key(session_a, session_b)` - a value both peers compute
  independently (each already knows its own session id and learns the
  peer's from the presence beacon `proximity.py` already tracks), order-
  independent so no handshake round-trip is needed. It identifies one
  specific pairing of *live badge instances*: a reveal captured from an
  A-vs-B encounter carries a key that only ever matches
  `encounter_key(A's session, B's session)`, never a third party's, and a
  reboot changes a badge's session id, so pre-reboot messages stop matching
  too.
- A **rank generation** counter, owned by whichever code holds "my current
  rank" (the redraw flow, settled below in `redraw.py` - see #3): starts at 0 for the rank
  dealt at kickoff, bumps every time that badge's rank is reassigned. Every
  reveal names the sender's current generation. `RevealGuard` remembers the
  highest generation it has already accepted per (peer mac, peer session)
  and rejects anything at or below that, so a reveal naming a rank the
  sender has since redrawn away from can't be replayed to fake a later
  result against the same peer either.

This settles #2 and unblocks #1: the wire format for a reveal message is
now `{mac, session, generation, rank_level, encounter_key}`, and
`RevealGuard.accept()` is the one gate every inbound reveal must pass before
its rank is trusted enough to call `engine.resolve()`.

## What's implemented (`radio.py`, `test_radio.py`)

**Settles #1.** `radio.py` is the over-the-air layer, split into two pieces
on purpose:

- `RadioAdapter` is transport-agnostic protocol/state-machine logic: it
  broadcasts the rank-free presence beacon on `send_beacon()`, feeds every
  inbound beacon into `ProximityTracker.seen()`/`.tick()`, and once
  `closest_ready()` names a peer, sends that peer (and only that peer) a
  point-to-point reveal built from `reveal.encounter_key()`. An inbound
  reveal is run through `RevealGuard.accept()`; once both this badge's own
  reveal has gone out and the peer's has passed the guard,
  `engine.resolve()` is called exactly once and the outcome is handed to a
  caller-supplied `on_result(peer_mac, outcome)` callback - applying that
  outcome to game state (removing pieces, triggering a redraw, ...) is left
  to #3/#4/#5, not this module. Transport is injected as a
  `send(mac, payload)` callable, which is what makes this half unit-
  testable (`test_radio.py`) without any real radio: a small in-process
  "world" wires two `RadioAdapter`s together and drives a full
  beacon-then-reveal-then-resolve exchange, including the replay/no-redraw
  edge cases `RevealGuard` is meant to catch.
- `ESPNowTransport` is the actual MicroPython `espnow`/`network` binding -
  thin on purpose, it only turns `espnow`'s send/recv into the
  `(mac, rssi, payload)` shape `RadioAdapter` expects. This half can't be
  unit tested off-device (no `espnow` module under CPython, no way to
  simulate real RSSI), which is the untestable piece #1 called out - see
  the manual test plan below.

Wire format is two pipe-delimited message types (no json dependency, keeps
payloads well under ESP-NOW's ~250 byte limit): a beacon is
`B|<mac>|<session>`, a reveal is
`R|<mac>|<session>|<generation>|<rank_level>|<encounter_key>` - the fields
issue `#2` settled, in the order `reveal.py` expects them.

### Manual/on-device test plan

Needs at least two real (or simulated) badges running MicroPython with
`espnow` support, since this is the one layer that can't be exercised under
plain CPython:

1. **Beacon send/receive** - two badges powered on near each other; confirm
   each sees the other show up in `tracker.peers` (log it) with a
   plausible RSSI, and that `peer.streak` climbs to `CLOSE_STREAK` as they
   stay close.
2. **Presence beacon stays rank-free** - sniff the air (or log every
   outbound `send_beacon()` payload) and confirm it only ever contains
   `mac`/`session`, never a rank, matching the security note in
   `proximity.py`.
3. **Reveal triggers exactly once per approach** - walk two badges together
   until `closest_ready()` fires; confirm both badges' `on_result` fires
   exactly once with the outcome `engine.resolve()` would produce for their
   two ranks, and that standing close afterward doesn't re-trigger it.
4. **Separate and re-approach** - step apart until RSSI drops and `tracker`
   ages the peer out or resets its streak, then re-approach: confirm no
   second resolve happens without a redraw (expected per the freshness
   design, see `RadioAdapter`'s docstring), matching
   `test_reapproaching_without_a_redraw_does_not_re_resolve`.
5. **Range/RSSI sanity** - confirm `CLOSE_DBM` in `proximity.py` is actually
   a reasonable "arm's length" threshold for the badges' real antennas
   (tune if two badges across a room falsely trigger, or two badges
   touching don't).
6. **`peers_table` availability** - confirm the running MicroPython/esp-idf
   build actually exposes `ESPNow.peers_table` for RSSI (see
   `ESPNowTransport._peer_rssi`'s fallback) - if it doesn't on the target
   port, closeness detection needs a different RSSI source before this is
   camp-ready.

## What's implemented (`redraw.py`, `test_redraw.py`)

**Decided (#3): physical round-trip, not instant reassignment.** Losing
(or drawing - `engine.BOTH_LOSE` counts too, both sides lose) disarms a
badge: it holds no live rank until it physically returns to its team's
base and gets in range of a base beacon, at which point it redraws. This
keeps the pacing the physical paper-card game already has - losing costs
you the walk back - matching the bias the rest of this project already has
toward keeping proximity and movement real (see `proximity.py`'s
continuous-broadcast design) rather than collapsing everything into pure
message-passing. The alternative (instant reassignment) was simpler and
more robust against a base beacon dying or dropping out of range mid-game,
but loses that pacing entirely - accepted as a known limitation instead:
run more than one base beacon per team so a single failed beacon doesn't
strand a team, the same way you wouldn't run a whole camp off one radio
anyway. This mirrors how the Bomb's stationary rule (RULES.md) is already
an honor-system limit this project accepts rather than tries to solve in
code.

A base isn't a new wire concept - it just broadcasts the same rank-free
presence beacon `radio.py` already defines (`encode_beacon()`), so
`proximity.ProximityTracker` sees it exactly like a player peer with no
changes to that module needed. What makes something a *base* rather than a
player is purely local: each badge is configured (at kickoff, alongside
issue `#5`'s rank distribution) with the set of its own team's base session ids/
macs.

Two pieces, both pure/testable in `redraw.py`:

- `RedrawState` holds one badge's own `rank_level`/`generation` (the same
  fields `radio.RadioAdapter` already exposes for exactly this purpose,
  see its docstring) plus a `disarmed` flag. `lose()` disarms it;
  `redraw(rng=random)` is a no-op while armed (so idling near base doesn't
  burn a redraw) and otherwise draws a fresh rank uniformly from
  `ranks.standard_army()` (so the odds match the physical game's piece
  counts) and bumps `generation` so `reveal.RevealGuard` rejects any stale
  reveal still naming the old rank.
- `BaseTracker` answers "am I close enough to a base to redraw right now,"
  reusing the same `ProximityTracker` closeness signal (streak ≥
  `CLOSE_STREAK`) player encounters already use rather than inventing a
  second one - a base's beacon is tracked in the exact same `tracker.peers`
  table as everyone else's.

Not solved here, left as a known simplification tied to #5 (army
distribution): `redraw()` draws independently each time rather than
tracking a shared pool of pieces already issued, so in principle (rare
with 59 pieces per side) two badges could simultaneously hold the same
rank after redraws - same as could already happen with the initial deal if
issue `#5`'s answer doesn't track a shared pool either.

Wiring `redraw.py` into `radio.RadioAdapter` (disarming on a losing
`on_result`, redrawing once `BaseTracker.at_base()` is true, and copying
the result back into `radio_adapter.rank_level`/`.generation`) is left to
the badge's main loop, not this module - matching how `RadioAdapter`
itself takes `rank_level`/`generation` as plain mutable fields rather than
owning their lifecycle.

## What's implemented (`flag.py`, `test_flag.py`)

**Decided (#4): a badge-carried flag holder, folded into the existing
rank/encounter machinery** (`ranks.py`, `engine.py`, `reveal.py`,
`radio.py`) rather than a separate wire concept, a fixed base-beacon
location, or leaving the flag physical/analog. The physical game's flag is
a hidden object one team must find - a designated player carrying a badge
that holds a special `ranks.FLAG` rank instead of a normal army piece is
the closest digital match, and "find and tag" is already exactly what the
existing proximity-then-reveal flow (`proximity.py` + `radio.py`) does for
ordinary encounters, so this needed **no new wire message and no new
proximity signal**. A fixed base-beacon location was rejected: it would
conflate "the flag" with `redraw.py`'s base concept (a team's redraw
point) and drops the "carried, must be tracked down" character the
physical game has. Staying physical/analog was rejected too, since the
game needs an actual digital win condition and everything else
camp-facing is already digitized.

`ranks.py` adds `FLAG` (level `-1`) and `FLAG_RANK` (`is_flag: True`),
deliberately kept out of `RANKS`/`standard_army()` - it's a single piece
assigned once per team at kickoff (tied to #5), never part of the shuffled
59-piece draw pool and never redrawn. `engine.resolve()` makes a Flag
always lose to any attacker, Bomb included (checked before the Bomb
special case, since a Flag has no Miner-style defense) - anyone who
reaches it captures it. The flag holder's badge is otherwise
indistinguishable from anyone else's: same rank-free presence beacon, same
one-time reveal exchange, so there's no way to spot it from a distance
before an encounter actually happens.

Unlike an ordinary loss, a captured flag holder does not get redrawn
(`redraw.py`) - the game is over for that side. That distinction is what
`flag.py` actually implements: `captured_sides(my_rank, peer_rank,
outcome)` inspects an already-resolved encounter (the same shape
`engine.resolve()` takes/returns) and reports which side(s), if any, just
had their flag captured (`{"self"}`, `{"peer"}`, both - the rare case of
two flag holders finding each other - or neither). This is the piece a
future main loop calls after `radio.RadioAdapter.on_result` fires, to
decide "redraw as usual" vs. "this side's game just ended," instead of
duplicating that reasoning inline.

Not solved here, left to #5 (army/rank distribution) and the badge's main
loop, same split `radio.py`/`redraw.py` already use: which player is
designated flag holder at kickoff, and what the main loop actually does
once a capture is recognised (announcing a winner, ending the game, ...).

## What's still open (game flow - not started)

Tracked as issues rather than just prose here, so this doesn't drift out of
sync with actual status:

- [#5 Who assigns ranks and distributes the army?](https://github.com/tjorim/levend-stratego-mpos/issues/5)
- [#6 Theming (mafia or otherwise)](https://github.com/tjorim/levend-stratego-mpos/issues/6) -
  deliberately deferred, not blocking anything above.

## Running the tests

```
python3 test_engine.py
python3 test_proximity.py
python3 test_reveal.py
python3 test_radio.py
python3 test_redraw.py
python3 test_flag.py
```

No dependencies - runs under plain CPython during design, and the same
`ranks.py`/`engine.py`/`proximity.py`/`reveal.py`/`radio.py`/`redraw.py`/`flag.py`
should run unmodified under MicroPython once wired into a badge app (`radio.py`'s
`ESPNowTransport` is the one piece that only actually runs on-device -
see its manual test plan above).
