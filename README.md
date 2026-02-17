# Treasure Sprint

Treasure Sprint is a small terminal game written in pure Python.

## Goal

Find the hidden treasure on a grid before your energy reaches zero.

## Controls

- `w` - move up
- `a` - move left
- `s` - move down
- `d` - move right
- `help` - show instructions
- `q` - quit

## Rules

- Every move costs 1 energy.
- Walking into a wall also costs 1 energy.
- Traps cost 2 extra energy.
- Coins give +25 score.
- Treasure gives a large bonus based on remaining energy.

## Run

```bash
python3 game.py
```

## Tests

```bash
python3 -m unittest discover -s tests -v
```
