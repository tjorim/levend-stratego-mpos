# levend-stratego-mpos

A badge-mediated take on [Levend Stratego](https://nl.scoutwiki.org/Levend_Stratego)
for [MicroPythonOS](https://github.com/MicroPythonOS/MicroPythonOS) — badges
hold your secret rank and resolve encounters over radio instead of paper
cards. Early design/prototype stage for a future Fri3d Camp edition.

**Status:** core rank hierarchy + encounter-resolution engine done and
tested (`ranks.py`, `engine.py`, `test_engine.py`). Badge/radio integration
and theming not started yet — see [`DESIGN.md`](DESIGN.md) for what's decided,
what's open, and sources for the physical game's rules.

```
python3 test_engine.py
```
