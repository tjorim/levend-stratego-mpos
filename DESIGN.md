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

## What's still open (radio adapter + game flow - not started)

The physical game has mechanics that don't map onto a badge 1:1 without a
decision. Notes so far, not commitments:

- **The actual ESP-NOW adapter.** `proximity.py` is deliberately radio-free
  and tested without hardware; something still needs to actually send/receive
  presence beacons and the point-to-point rank-reveal exchange over ESP-NOW,
  call into `ProximityTracker` and `engine.resolve()`, and apply the outcome.
  Untested until it's running on real (or simulated) badges.
- **Reveal-exchange freshness.** Once two peers are close, both need to send
  their rank to each other once, resolve, and apply the outcome exactly once
  - and a stale/replayed message (e.g. from a peer that already lost and
  redrew) shouldn't be able to fake a result. Needs something like Foxhunt's
  `encounter_key` (a value derived from both sides' session ids, so both
  peers agree on the same one-shot key for a given approach) plus a rank
  "generation" counter that bumps every time a badge redraws, so an old
  reveal can't be replayed after the rank it named is no longer live.
- **"Return to base for a new card."** In the physical game, losing your
  encounter means walking back to base and drawing a new random rank - that
  round-trip is part of what makes it an *active outdoor* game, not just an
  app. Digitally, does losing require physically reaching a base beacon to
  redraw (preserves the physical pacing), or does the badge just reassign
  instantly (loses that pacing, but removes a failure mode where a base
  beacon is out of range/dead)?
- **Flag capture.** The physical flag is a real hidden object. Digital
  equivalent candidates: a badge carried by a designated "flag holder" that
  the other team must find and tag; a fixed base-beacon representing the
  flag's position; or keep the flag physical and only digitize rank combat.
- **Team assignment & army distribution.** Who assigns ranks - a game-master
  badge/console distributing the shuffled army over the air at kickoff, or
  does each badge just self-assign from a shared seed? Affects whether cheating
  (peeking at your own rank before choosing when to reveal it, which is
  already possible in the physical game too) needs any mitigation.
- **Theming.** "Maffiakamp" turned out to be undocumented online beyond a
  one-line pitch on Scoutpedia (mafia-family ranks/statuses, no published
  hierarchy) - see the chat history for the full research. Any theme is just
  a new `RANKS`-shaped list once the engine's stable, so this is deliberately
  not blocking the core work.

## Running the tests

```
python3 test_engine.py
python3 test_proximity.py
```

No dependencies - runs under plain CPython during design, and the same
`ranks.py`/`engine.py`/`proximity.py` should run unmodified under MicroPython
once wired into a badge app.
