from __future__ import annotations

from dataclasses import dataclass, field
from random import Random
from typing import Sequence


CARD_EVENT = "event"
CARD_MONSTER = "monster"


@dataclass(frozen=True, slots=True)
class EventTemplate:
    name: str
    effect_id: str
    description: str
    potency: int


@dataclass(frozen=True, slots=True)
class MonsterTemplate:
    name: str
    description: str
    base_danger: int
    reward: int


@dataclass(frozen=True, slots=True)
class Card:
    name: str
    card_type: str
    description: str
    danger: int = 0
    reward: int = 0
    effect_id: str = ""
    potency: int = 0


@dataclass(slots=True)
class Hero:
    name: str
    hp: int
    power: int

    @property
    def alive(self) -> bool:
        return self.hp > 0


@dataclass(frozen=True, slots=True)
class GameConfig:
    party_names: tuple[str, str, str] = ("Warrior", "Mage", "Rogue")
    hero_hp: int = 14
    hero_power: int = 2
    max_rooms: int = 6
    playable_cards: int = 2
    hand_event_cards: int = 2
    hand_monster_cards: int = 3


@dataclass(slots=True)
class GameState:
    config: GameConfig
    party: list[Hero]
    rng: Random = field(repr=False)
    room: int = 1
    score: int = 0
    last_event: str = "Draw cards and play exactly two."
    history: list[str] = field(default_factory=list)

    @property
    def survivors(self) -> int:
        return sum(1 for hero in self.party if hero.alive)

    @property
    def party_defeated(self) -> bool:
        return self.survivors == 0

    @property
    def campaign_complete(self) -> bool:
        return self.room > self.config.max_rooms

    @property
    def is_over(self) -> bool:
        return self.party_defeated or self.campaign_complete


EVENT_TEMPLATES: tuple[EventTemplate, ...] = (
    EventTemplate(
        name="Campfire Respite",
        effect_id="campfire",
        description="All living heroes recover 2 HP.",
        potency=2,
    ),
    EventTemplate(
        name="Ceiling Trap",
        effect_id="trap",
        description="All living heroes take 2 damage.",
        potency=2,
    ),
    EventTemplate(
        name="Hidden Cache",
        effect_id="cache",
        description="One random living hero recovers 4 HP.",
        potency=4,
    ),
    EventTemplate(
        name="Dark Omen",
        effect_id="omen",
        description="One random living hero takes 4 damage.",
        potency=4,
    ),
)

MONSTER_TEMPLATES: tuple[MonsterTemplate, ...] = (
    MonsterTemplate(
        name="Goblin Ambush",
        description="Quick raiders strike from both sides.",
        base_danger=1,
        reward=14,
    ),
    MonsterTemplate(
        name="Skeleton Knight",
        description="A disciplined undead duelist blocks the corridor.",
        base_danger=2,
        reward=20,
    ),
    MonsterTemplate(
        name="Ogre Brute",
        description="A heavy hitter with room-wide threat.",
        base_danger=3,
        reward=26,
    ),
    MonsterTemplate(
        name="Cult Warlock",
        description="Ritual magic weakens the party's defense.",
        base_danger=2,
        reward=22,
    ),
    MonsterTemplate(
        name="Cave Stalker",
        description="A silent predator from the shadows.",
        base_danger=1,
        reward=16,
    ),
)


def create_game(config: GameConfig | None = None, seed: int | None = None) -> GameState:
    config = config or GameConfig()
    if len(config.party_names) != 3:
        raise ValueError("Campaign requires exactly 3 heroes.")
    if config.hand_event_cards != 2 or config.hand_monster_cards != 3:
        raise ValueError("Hand must contain 2 event cards and 3 monster cards.")
    if config.playable_cards != 2:
        raise ValueError("Exactly 2 cards must be played per round.")

    party = [
        Hero(name=name, hp=config.hero_hp, power=config.hero_power)
        for name in config.party_names
    ]
    return GameState(config=config, party=party, rng=Random(seed))


def draw_hand(state: GameState) -> list[Card]:
    event_templates = state.rng.sample(EVENT_TEMPLATES, k=state.config.hand_event_cards)
    monster_templates = state.rng.sample(MONSTER_TEMPLATES, k=state.config.hand_monster_cards)

    cards = [
        Card(
            name=template.name,
            card_type=CARD_EVENT,
            description=template.description,
            effect_id=template.effect_id,
            potency=template.potency,
        )
        for template in event_templates
    ]

    for template in monster_templates:
        danger = template.base_danger + (state.room - 1) // 2
        reward = template.reward + (state.room - 1) * 3
        cards.append(
            Card(
                name=template.name,
                card_type=CARD_MONSTER,
                description=template.description,
                danger=danger,
                reward=reward,
            )
        )

    state.rng.shuffle(cards)
    return cards


def parse_card_selection(
    raw_command: str,
    hand_size: int,
    playable_cards: int = 2,
) -> tuple[tuple[int, ...] | None, str | None]:
    tokens = raw_command.replace(",", " ").split()
    if len(tokens) != playable_cards:
        return None, f"Choose exactly {playable_cards} cards."

    try:
        picked = tuple(int(token) - 1 for token in tokens)
    except ValueError:
        return None, "Card picks must be numbers."

    if len(set(picked)) != playable_cards:
        return None, "You cannot play the same card twice."

    if any(index < 0 or index >= hand_size for index in picked):
        return None, f"Card index must be between 1 and {hand_size}."

    return picked, None


def _living_heroes(state: GameState) -> list[Hero]:
    return [hero for hero in state.party if hero.alive]


def _change_hero_hp(state: GameState, hero: Hero, delta: int) -> None:
    next_hp = hero.hp + delta
    hero.hp = min(max(next_hp, 0), state.config.hero_hp)


def _apply_event_card(state: GameState, card: Card) -> str:
    living = _living_heroes(state)
    if not living:
        return "No heroes are alive to resolve this event."

    if card.effect_id == "campfire":
        for hero in living:
            _change_hero_hp(state, hero, card.potency)
        state.score += 8
        return "The party regroups and recovers health."

    if card.effect_id == "trap":
        for hero in living:
            _change_hero_hp(state, hero, -card.potency)
        state.score -= 4
        return "A trap goes off and injures every hero."

    target = state.rng.choice(living)
    if card.effect_id == "cache":
        _change_hero_hp(state, target, card.potency)
        state.score += 10
        return f"{target.name} finds supplies and recovers health."

    _change_hero_hp(state, target, -card.potency)
    state.score += 2
    return f"{target.name} suffers from a dark omen."


def _apply_monster_card(state: GameState, card: Card) -> str:
    living = _living_heroes(state)
    if not living:
        return "No heroes remain to face monsters."

    party_roll = sum(state.rng.randint(1, 6) + hero.power for hero in living)
    monster_roll = state.rng.randint(1, 6) + card.danger * 3 + max(0, state.room - 1)

    if party_roll >= monster_roll:
        state.score += card.reward
        margin = party_roll - monster_roll
        if margin <= 2:
            target = state.rng.choice(living)
            _change_hero_hp(state, target, -1)
            return f"The party defeats {card.name}, but {target.name} loses 1 HP."
        return f"The party defeats {card.name}."

    damage = max(1, card.danger)
    for hero in living:
        _change_hero_hp(state, hero, -damage)
    state.score -= 6 * card.danger
    return f"{card.name} overwhelms the party. Every hero loses {damage} HP."


def resolve_card(state: GameState, card: Card) -> str:
    if card.card_type == CARD_EVENT:
        return _apply_event_card(state, card)
    if card.card_type == CARD_MONSTER:
        return _apply_monster_card(state, card)
    raise ValueError(f"Unknown card type: {card.card_type}")


def play_selected_cards(
    state: GameState,
    hand: Sequence[Card],
    picked_indexes: Sequence[int],
) -> list[str]:
    if len(picked_indexes) != state.config.playable_cards:
        raise ValueError(f"Exactly {state.config.playable_cards} cards must be played.")
    if len(set(picked_indexes)) != len(picked_indexes):
        raise ValueError("Card picks must be unique.")
    if any(index < 0 or index >= len(hand) for index in picked_indexes):
        raise ValueError("Card pick is out of hand bounds.")

    messages: list[str] = []
    for index in picked_indexes:
        card = hand[index]
        result = resolve_card(state, card)
        label = card.card_type.upper()
        messages.append(f"{label} - {card.name}: {result}")
        if state.party_defeated:
            messages.append("All heroes are down. The campaign fails here.")
            break

    if not state.party_defeated:
        state.room += 1
        if state.campaign_complete:
            bonus = state.survivors * 25
            state.score += bonus
            messages.append(f"Campaign complete. Survivor bonus: +{bonus} score.")

    state.last_event = " ".join(messages)
    state.history.extend(messages)
    return messages


def format_status(state: GameState) -> str:
    return (
        f"Room: {state.room}/{state.config.max_rooms} | "
        f"Survivors: {state.survivors}/3 | Score: {state.score}"
    )


def format_party(state: GameState) -> str:
    return ", ".join(f"{hero.name}:{hero.hp}HP" for hero in state.party)


def render_hand(hand: Sequence[Card]) -> str:
    rows: list[str] = []
    for index, card in enumerate(hand, start=1):
        if card.card_type == CARD_EVENT:
            extra = f"effect={card.effect_id}"
        else:
            extra = f"danger={card.danger}, reward={card.reward}"
        rows.append(f"{index}. [{card.card_type}] {card.name} ({extra}) - {card.description}")
    return "\n".join(rows)


def print_instructions() -> None:
    print(
        "\nYou are the Game Master of a 3-hero campaign.\n"
        "Each room gives you 5 cards: 2 events and 3 monsters.\n"
        "You can play exactly 2 cards per room.\n\n"
        "Commands:\n"
        "  <n1> <n2> - play two cards by number (example: 1 4)\n"
        "  help - show instructions\n"
        "  q - quit game\n"
    )


def run_game(seed: int | None = None) -> int:
    state = create_game(seed=seed)
    print("=== Dungeon Master Roguelike ===")
    print_instructions()

    while not state.is_over:
        hand = draw_hand(state)
        print("")
        print(format_status(state))
        print(f"Party: {format_party(state)}")
        print("Hand (2 event cards + 3 monster cards):")
        print(render_hand(hand))

        while True:
            raw_command = input("Choose 2 cards, help, or q: ").strip().lower()

            if raw_command in {"q", "quit", "exit"}:
                print("Campaign ended by Game Master.")
                return state.score

            if raw_command in {"help", "h"}:
                print_instructions()
                continue

            picked, error = parse_card_selection(
                raw_command,
                hand_size=len(hand),
                playable_cards=state.config.playable_cards,
            )
            if error:
                print(error)
                continue

            assert picked is not None
            messages = play_selected_cards(state, hand, picked)
            for message in messages:
                print(f"- {message}")
            break

    print("")
    print("=== Campaign Result ===")
    print(f"Final party: {format_party(state)}")
    if state.campaign_complete and not state.party_defeated:
        print(f"Victory! Final score: {state.score}")
    else:
        print(f"Defeat. Final score: {state.score}")
    return state.score


if __name__ == "__main__":
    run_game()
