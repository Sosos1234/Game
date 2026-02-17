import unittest

from game import (
    CARD_EVENT,
    CARD_MONSTER,
    Card,
    GameConfig,
    create_game,
    draw_hand,
    parse_card_selection,
    play_selected_cards,
    resolve_card,
)


class RoguelikeGameTests(unittest.TestCase):
    def test_create_game_starts_with_three_heroes(self) -> None:
        state = create_game(seed=1)
        self.assertEqual(len(state.party), 3)
        self.assertEqual(state.survivors, 3)

    def test_draw_hand_has_2_event_and_3_monster_cards(self) -> None:
        state = create_game(seed=10)
        hand = draw_hand(state)

        self.assertEqual(len(hand), 5)
        self.assertEqual(sum(card.card_type == CARD_EVENT for card in hand), 2)
        self.assertEqual(sum(card.card_type == CARD_MONSTER for card in hand), 3)

    def test_parse_card_selection_accepts_exactly_two_unique_picks(self) -> None:
        picks, error = parse_card_selection("1 4", hand_size=5, playable_cards=2)
        self.assertEqual(picks, (0, 3))
        self.assertIsNone(error)

    def test_parse_card_selection_rejects_invalid_input(self) -> None:
        picks, error = parse_card_selection("2 2", hand_size=5, playable_cards=2)
        self.assertIsNone(picks)
        self.assertIn("cannot play the same card twice", error or "")

        picks, error = parse_card_selection("1 2 3", hand_size=5, playable_cards=2)
        self.assertIsNone(picks)
        self.assertIn("exactly 2 cards", error or "")

    def test_play_selected_cards_requires_exactly_two_cards(self) -> None:
        state = create_game(seed=11)
        hand = draw_hand(state)
        with self.assertRaises(ValueError):
            play_selected_cards(state, hand, (0,))

    def test_campfire_event_recovers_party_hp(self) -> None:
        config = GameConfig(hero_hp=10)
        state = create_game(config=config, seed=5)
        for hero in state.party:
            hero.hp = 5

        card = Card(
            name="Campfire Respite",
            card_type=CARD_EVENT,
            description="All living heroes recover 2 HP.",
            effect_id="campfire",
            potency=2,
        )
        resolve_card(state, card)

        self.assertEqual([hero.hp for hero in state.party], [7, 7, 7])

    def test_low_danger_monster_is_beaten_by_strong_party(self) -> None:
        config = GameConfig(hero_hp=12, hero_power=5)
        state = create_game(config=config, seed=7)
        card = Card(
            name="Training Beast",
            card_type=CARD_MONSTER,
            description="A very weak foe.",
            danger=0,
            reward=9,
        )
        resolve_card(state, card)

        self.assertGreaterEqual(state.score, 9)
        self.assertEqual([hero.hp for hero in state.party], [12, 12, 12])


if __name__ == "__main__":
    unittest.main()
