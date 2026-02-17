# Dungeon Master Roguelike

Terminal roguelike in pure Python where you play as the Game Master of a small campaign.

## Core idea

- You lead a party of exactly 3 heroes.
- Each room gives you 5 cards:
  - 2 event cards
  - 3 monster cards
- You are allowed to play only 2 cards from the hand.
- Keep at least one hero alive until the campaign is completed.

## Controls

- `<n1> <n2>` - play two cards by number, for example `1 4`
- `help` - print instructions
- `q` - quit

## Run

```bash
python3 game.py
```

## Tests

```bash
python3 -m unittest discover -s tests -v
```
