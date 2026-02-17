from __future__ import annotations

from dataclasses import dataclass, field
from random import Random


DIRECTION_DELTAS = {
    "w": (-1, 0),
    "a": (0, -1),
    "s": (1, 0),
    "d": (0, 1),
}


@dataclass(frozen=True, slots=True)
class Position:
    row: int
    col: int

    def move(self, row_delta: int, col_delta: int) -> "Position":
        return Position(self.row + row_delta, self.col + col_delta)


@dataclass(frozen=True, slots=True)
class GameConfig:
    board_size: int = 5
    trap_count: int = 4
    coin_count: int = 3
    starting_energy: int = 14


@dataclass(slots=True)
class GameState:
    config: GameConfig
    player: Position
    treasure: Position
    traps: set[Position]
    coins: set[Position]
    energy: int
    score: int = 0
    found_treasure: bool = False
    visited: set[Position] = field(default_factory=set)
    last_event: str = "Use WASD to move. Type 'help' to print instructions."

    @property
    def is_over(self) -> bool:
        return self.found_treasure or self.energy <= 0

    def in_bounds(self, position: Position) -> bool:
        return 0 <= position.row < self.config.board_size and 0 <= position.col < self.config.board_size


def _pick_positions(
    rng: Random,
    board_size: int,
    amount: int,
    blocked: set[Position],
) -> set[Position]:
    chosen: set[Position] = set()
    while len(chosen) < amount:
        candidate = Position(rng.randrange(board_size), rng.randrange(board_size))
        if candidate not in blocked and candidate not in chosen:
            chosen.add(candidate)
    return chosen


def create_game(config: GameConfig | None = None, seed: int | None = None) -> GameState:
    config = config or GameConfig()
    rng = Random(seed)

    start = Position(config.board_size // 2, config.board_size // 2)

    treasure = next(iter(_pick_positions(rng, config.board_size, 1, {start})))
    blocked = {start, treasure}
    traps = _pick_positions(rng, config.board_size, config.trap_count, blocked)
    blocked.update(traps)
    coins = _pick_positions(rng, config.board_size, config.coin_count, blocked)

    return GameState(
        config=config,
        player=start,
        treasure=treasure,
        traps=traps,
        coins=coins,
        energy=config.starting_energy,
        visited={start},
    )


def apply_move(state: GameState, direction: str) -> None:
    direction = direction.strip().lower()
    if direction not in DIRECTION_DELTAS:
        state.last_event = "Unknown command. Use w/a/s/d to move or 'help'."
        return

    row_delta, col_delta = DIRECTION_DELTAS[direction]
    next_pos = state.player.move(row_delta, col_delta)

    if not state.in_bounds(next_pos):
        state.energy -= 1
        state.last_event = "You hit a wall and lost 1 energy."
        return

    state.player = next_pos
    state.visited.add(next_pos)
    state.energy -= 1

    events: list[str] = ["You moved safely."]

    if next_pos in state.coins:
        state.coins.remove(next_pos)
        state.score += 25
        events.append("Coin found (+25 score).")

    if next_pos in state.traps:
        state.energy -= 2
        events.append("Trap triggered (-2 extra energy).")

    if next_pos == state.treasure:
        state.found_treasure = True
        bonus = 100 + max(state.energy, 0) * 5
        state.score += bonus
        events.append(f"Treasure found! Bonus +{bonus} score.")

    if state.energy <= 0 and not state.found_treasure:
        events.append("You ran out of energy.")

    state.last_event = " ".join(events)


def render_map(state: GameState, reveal_hidden: bool = False) -> str:
    rows: list[str] = []
    for row in range(state.config.board_size):
        cells: list[str] = []
        for col in range(state.config.board_size):
            pos = Position(row, col)
            if pos == state.player:
                cells.append("P")
                continue

            if reveal_hidden:
                if pos == state.treasure and not state.found_treasure:
                    cells.append("T")
                elif pos in state.traps:
                    cells.append("X")
                elif pos in state.coins:
                    cells.append("C")
                elif pos in state.visited:
                    cells.append(".")
                else:
                    cells.append("_")
                continue

            if pos in state.visited:
                cells.append(".")
            else:
                cells.append("?")

        rows.append(" ".join(cells))
    return "\n".join(rows)


def format_status(state: GameState) -> str:
    return f"Energy: {state.energy} | Score: {state.score} | Coins left: {len(state.coins)}"


def print_instructions() -> None:
    print(
        "\nGoal: find the hidden treasure before your energy reaches zero.\n"
        "Commands:\n"
        "  w - move up\n"
        "  a - move left\n"
        "  s - move down\n"
        "  d - move right\n"
        "  help - show instructions\n"
        "  q - quit game\n\n"
        "Rules:\n"
        "- Every move costs 1 energy.\n"
        "- Stepping on a trap costs 2 more energy.\n"
        "- Coins give +25 score.\n"
        "- Finding treasure gives a large bonus based on remaining energy.\n"
    )


def run_game(seed: int | None = None) -> int:
    state = create_game(seed=seed)
    print("=== Treasure Sprint ===")
    print_instructions()

    while not state.is_over:
        print(render_map(state))
        print(format_status(state))
        print(f"Last event: {state.last_event}")
        command = input("Move (w/a/s/d, help, q): ").strip().lower()

        if command in {"q", "quit", "exit"}:
            print("Game cancelled.")
            return state.score

        if command in {"help", "h"}:
            print_instructions()
            continue

        apply_move(state, command)
        print("")

    print("Final map:")
    print(render_map(state, reveal_hidden=True))
    if state.found_treasure:
        print(f"You win! Final score: {state.score}")
    else:
        print("You lose. No energy left.")
        print(f"Final score: {state.score}")
    return state.score


if __name__ == "__main__":
    run_game()
