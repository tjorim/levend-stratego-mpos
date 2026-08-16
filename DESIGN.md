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

## What's still open (badge/radio layer - not started)

The physical game has mechanics that don't map onto a badge 1:1 without a
decision. Notes so far, not commitments:

- **Encounter trigger.** Two existing patterns already exist in this account's
  other repos: `foxhunt-recovered`'s `snuffel_link.py` does continuous
  broadcast + a peer table with RSSI-smoothed "closeness" (N consecutive
  close readings before triggering); `bomberboy-mpos`'s `network_play.py`
  does an explicit async-paired `EspNowLink` handshake. Continuous broadcast
  matches the physical game's "just bump into someone" feel better; a paired
  handshake is simpler and more deliberate. Undecided.
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
```

No dependencies - runs under plain CPython during design, and the same
`ranks.py`/`engine.py` should run unmodified under MicroPython once wired
into a badge app.
