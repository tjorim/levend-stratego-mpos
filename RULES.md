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

**The rule: higher rank wins. Equal ranks meeting: both lose.** The Marshal
is the top of the ladder, but that does *not* mean it beats everything — it
has two losses, same as everyone else has some. Three exceptions to learn by
heart, since they're the only ranks that don't simply follow the ladder:

- **The Spy loses to everything — except the Marshal, who it beats.** Not
  just "weak with one trick": a Spy vs. anyone other than the Marshal loses
  the normal way, ladder position and all.
- **The Bomb beats every single rank, Marshal included — except the Miner,
  who defuses it and wins.** The Bomb's ladder position doesn't matter at
  all; this overrides everything else, even the Spy-vs-Marshal exception (a
  Spy meeting a Bomb loses, same as anyone else would). So the Marshal's two
  losses are the Spy and the Bomb — the Miner is the only rank that's never
  at risk from either of them.
- **The Bomb never moves once placed** — it's stationed, not carried around
  looking for encounters. Worth being upfront that this is an honor-system
  rule, not something the badge can enforce: proximity detection only knows
  who's near whom, not who's holding still versus wandering. Same limitation
  the physical paper-card game already has — nothing stops a Bomb-card
  holder from walking around there either, beyond "please don't, that's the
  rule."

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

## Losing an encounter

Lose — or draw; a tie means *both* of you lose — and your badge locks you
out. You're not carrying a live rank anymore, so you can't trigger (or be
part of) another encounter until you walk back to your team's base and get
in range of a base beacon there, which draws you a brand new random rank
from the same odds everyone started with. That's the same pacing the
paper-card original has: losing costs you the walk back, not just a tap on
a screen.

If your team's base only has one beacon, ask whoever's running the game —
camps should run more than one per team, so a dead battery or a beacon
that's briefly out of range doesn't strand anyone mid-game.

## Winning the game

One player per team is secretly designated the flag holder at kickoff — a
teammate rather than an object, carrying the flag on their badge instead of
a normal rank. The other team wins by finding and encountering them, the
same way any other encounter happens: walk close enough, badges compare
ranks automatically. The flag holder's badge looks exactly like everyone
else's from a distance — there's no way to spot who's carrying it before
you actually meet them.

The Flag always loses when found, no matter who finds it (even a Bomb
captures it) — there's no way to defend it by rank. Unlike an ordinary
loss, a captured flag holder doesn't walk back to base and redraw: that
team's game is over.

## Getting your rank at the start

There's no game-master badge handing out ranks, and no shared code to punch
in either — every badge draws its own rank itself, the moment it's turned on
at kickoff, from the same odds everyone else's badge is drawing from. Whoever
you're playing against has no way to know what you drew until you actually
meet them.

One player per team is set up ahead of time (by whoever's running the game)
as that team's flag holder instead of drawing an army rank — see "Winning
the game" above.

Nothing stops you from peeking at your own rank the moment it's assigned —
same as you could always peek at your own card in the paper version. This
game doesn't try to stop you from knowing your own rank, only from other
people learning it before they meet you.

## Setup & logistics

Not written yet — group size, terrain requirements, game duration, how teams
are split. Will fill in once the mechanics above are settled enough to know
what's actually needed on the day.
