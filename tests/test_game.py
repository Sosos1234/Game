import unittest

from game import GameConfig, GameState, Position, apply_move, create_game


class GameLogicTests(unittest.TestCase):
    def test_create_game_places_objects_without_overlap(self) -> None:
        config = GameConfig(board_size=5, trap_count=4, coin_count=3, starting_energy=10)
        state = create_game(config=config, seed=11)

        start = Position(2, 2)
        self.assertEqual(state.player, start)
        self.assertNotEqual(state.treasure, start)
        self.assertEqual(len(state.traps), 4)
        self.assertEqual(len(state.coins), 3)

        occupied = {start, state.treasure} | state.traps | state.coins
        self.assertEqual(len(occupied), 1 + 1 + 4 + 3)

    def test_invalid_command_does_not_change_energy_or_position(self) -> None:
        state = self._make_state(energy=5)
        apply_move(state, "x")

        self.assertEqual(state.player, Position(1, 1))
        self.assertEqual(state.energy, 5)

    def test_hitting_wall_costs_energy_and_stays_in_place(self) -> None:
        state = self._make_state(energy=5, start=Position(0, 0))
        apply_move(state, "w")

        self.assertEqual(state.player, Position(0, 0))
        self.assertEqual(state.energy, 4)

    def test_coin_increases_score_and_is_removed(self) -> None:
        coin = Position(1, 2)
        state = self._make_state(energy=5, coins={coin})
        apply_move(state, "d")

        self.assertEqual(state.player, coin)
        self.assertEqual(state.energy, 4)
        self.assertEqual(state.score, 25)
        self.assertNotIn(coin, state.coins)

    def test_trap_costs_extra_energy(self) -> None:
        trap = Position(1, 2)
        state = self._make_state(energy=5, traps={trap})
        apply_move(state, "d")

        self.assertEqual(state.player, trap)
        self.assertEqual(state.energy, 2)

    def test_treasure_sets_victory_and_adds_bonus_score(self) -> None:
        treasure = Position(1, 2)
        state = self._make_state(energy=5, treasure=treasure)
        apply_move(state, "d")

        self.assertTrue(state.found_treasure)
        self.assertEqual(state.energy, 4)
        self.assertEqual(state.score, 120)

    @staticmethod
    def _make_state(
        energy: int,
        start: Position = Position(1, 1),
        treasure: Position = Position(2, 2),
        traps: set[Position] | None = None,
        coins: set[Position] | None = None,
    ) -> GameState:
        config = GameConfig(board_size=3, trap_count=0, coin_count=0, starting_energy=energy)
        return GameState(
            config=config,
            player=start,
            treasure=treasure,
            traps=traps or set(),
            coins=coins or set(),
            energy=energy,
            visited={start},
        )


if __name__ == "__main__":
    unittest.main()
