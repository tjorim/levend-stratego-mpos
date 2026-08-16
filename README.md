# levend-stratego-mpos

A badge-mediated take on [Levend Stratego](https://nl.scoutwiki.org/Levend_Stratego)
for [MicroPythonOS](https://github.com/MicroPythonOS/MicroPythonOS) — badges
hold your secret rank and resolve encounters over radio instead of paper
cards. Early design/prototype stage for a future Fri3d Camp edition.

**Status:** core rank hierarchy + encounter-resolution engine
(`ranks.py`, `engine.py`) and proximity/closeness detection (`proximity.py`)
done and tested. ESP-NOW radio adapter, game flow, and theming not started
yet — see [`DESIGN.md`](DESIGN.md) for what's decided, what's open, and
sources for the physical game's rules.

```
python3 test_engine.py
python3 test_proximity.py
```
