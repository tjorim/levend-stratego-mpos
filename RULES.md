# How to play

A living-rules document for the game itself, written for whoever's running or
playing it at camp — not for the code. See [`DESIGN.md`](DESIGN.md) for the
engineering side (how the badge implements all this).

Sections marked 🚧 aren't decided yet — they link to the open issue tracking
that decision. Everything else below is settled and already built.

## The idea

Two teams spread out across a shared outdoor area. Every player secretly
holds a rank on their badge. Walk close enough to an opposing player and your
badges quietly compare ranks and settle the encounter for you — no cards, no
"I definitely showed you the right one, I promise."

## Ranks

Every player is secretly assigned one of these on their badge at the start of
the game, from highest to lowest:

Marshal (1 per team) → General (4) → Major (6) → Captain (7) → Lieutenant (8)
→ Sergeant (9) → Miner (6) → Scout (10) → Spy (2)

Plus the Bomb (6 per team), which sits outside the ladder entirely — see
below. 59 ranks per team in total.

**The rule: higher rank wins. Equal ranks meeting: both lose.** Three
exceptions to learn by heart, since they're the only ranks that *don't*
simply follow the ladder above:

- **The Spy loses to everything — except the Marshal, who it beats.** Not
  just "weak with one trick": a Spy vs. anyone other than the Marshal loses
  the normal way, ladder position and all.
- **The Bomb beats every single rank, Marshal included — except the Miner,
  who defuses it and wins.** The Bomb's ladder position doesn't matter at
  all; this overrides everything else, even the Spy-vs-Marshal exception (a
  Spy meeting a Bomb loses, same as anyone else would).
- **The Bomb never moves once placed** — it's stationed, not carried around
  looking for encounters.

If you want the full beats/loses breakdown per rank rather than reasoning it
out from the two rules above, `python3 -c "from ranks import RANKS; from
engine import resolve"` and a short loop will print it — or just ask whoever's
working on the code.

## How an encounter happens

Your badge is always quietly listening for other badges nearby. Once you've
been close enough to the same opposing player for a few seconds straight
(not just a passing brush), your badges trigger an encounter automatically
and privately compare ranks — you'll only know the outcome, not the process.
Step away and come back later, and a fresh encounter can trigger again with
the same person.

Your rank stays completely private the rest of the time — your badge never
broadcasts it, so there's no way for anyone (badge-owning or not) to scan the
area and learn who's weak or strong before actually meeting them. That's true
to the physical game too, where the only way to learn someone's rank is to
actually meet them and reveal.

## 🚧 Losing an encounter

[Issue #3](https://github.com/tjorim/levend-stratego-mpos/issues/3) — not
decided yet whether you need to physically walk back to a base to get a new
rank (matching the physical game's pacing) or your badge just reassigns you
one on the spot.

## 🚧 Winning the game

[Issue #4](https://github.com/tjorim/levend-stratego-mpos/issues/4) — flag
capture mechanic not decided yet: whether the flag is a badge someone
carries, a fixed beacon location, or stays a real physical object like the
original game and only the rank combat is digitized.

## 🚧 Getting your rank at the start

[Issue #5](https://github.com/tjorim/levend-stratego-mpos/issues/5) — not
decided whether a game-master badge hands out the shuffled army at kickoff,
or badges self-assign from a shared seed.

## Setup & logistics

Not written yet — group size, terrain requirements, game duration, how teams
are split. Will fill in once the mechanics above are settled enough to know
what's actually needed on the day.
