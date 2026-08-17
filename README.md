# levend-stratego-mpos

A badge-mediated take on [Levend Stratego](https://nl.scoutwiki.org/Levend_Stratego)
for [MicroPythonOS](https://github.com/MicroPythonOS/MicroPythonOS) — badges
hold your secret rank and resolve encounters over radio instead of paper
cards. Early design/prototype stage for a future Fri3d Camp edition.

**Status:** core rank hierarchy + encounter-resolution engine
(`ranks.py`, `engine.py`), proximity/closeness detection (`proximity.py`),
reveal-exchange freshness / anti-replay (`reveal.py`), and the ESP-NOW radio
adapter (`radio.py`) done and tested. Game flow and theming not started yet.

- [`RULES.md`](RULES.md) — how the game actually plays, for whoever's running
  or playing it at camp.
- [`DESIGN.md`](DESIGN.md) — the engineering side: what's decided, what's
  open (tracked as [issues](https://github.com/tjorim/levend-stratego-mpos/issues)),
  sources for the physical game's rules.

```
python3 test_engine.py
python3 test_proximity.py
python3 test_reveal.py
python3 test_radio.py
```
