from __future__ import annotations

import base64
import json
import pickle
import random
import tkinter as tk
from dataclasses import asdict
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk
from typing import Any

from game import (
    CARD_EVENT,
    CARD_MONSTER,
    Card,
    GameConfig,
    GameState,
    create_game,
    draw_hand,
    format_status,
    play_selected_cards,
)


SAVE_FILE_NAME = "save_slot.json"


def _card_to_dict(card: Card) -> dict[str, Any]:
    return {
        "name": card.name,
        "card_type": card.card_type,
        "description": card.description,
        "danger": card.danger,
        "reward": card.reward,
        "effect_id": card.effect_id,
        "potency": card.potency,
    }


def _card_from_dict(payload: dict[str, Any]) -> Card:
    return Card(
        name=str(payload["name"]),
        card_type=str(payload["card_type"]),
        description=str(payload["description"]),
        danger=int(payload.get("danger", 0)),
        reward=int(payload.get("reward", 0)),
        effect_id=str(payload.get("effect_id", "")),
        potency=int(payload.get("potency", 0)),
    )


def _encode_rng_state(state: object) -> str:
    raw = pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL)
    return base64.b64encode(raw).decode("ascii")


def _decode_rng_state(payload: str) -> object:
    raw = base64.b64decode(payload.encode("ascii"))
    return pickle.loads(raw)


def serialize_campaign(state: GameState, hand: list[Card]) -> dict[str, Any]:
    return {
        "config": asdict(state.config),
        "party": [asdict(hero) for hero in state.party],
        "room": state.room,
        "score": state.score,
        "last_event": state.last_event,
        "history": list(state.history),
        "hand": [_card_to_dict(card) for card in hand],
        "rng_state": _encode_rng_state(state.rng.getstate()),
    }


def deserialize_campaign(payload: dict[str, Any]) -> tuple[GameState, list[Card]]:
    raw_config = dict(payload["config"])
    raw_config["party_names"] = tuple(raw_config["party_names"])
    config = GameConfig(**raw_config)
    state = create_game(config=config)

    heroes_payload = payload["party"]
    if len(heroes_payload) != 3:
        raise ValueError("Save data is invalid: expected exactly 3 heroes.")

    for hero, hero_payload in zip(state.party, heroes_payload):
        hero.name = str(hero_payload["name"])
        hero.hp = int(hero_payload["hp"])
        hero.power = int(hero_payload["power"])

    state.room = int(payload["room"])
    state.score = int(payload["score"])
    state.last_event = str(payload.get("last_event", "Loaded campaign."))
    state.history = [str(item) for item in payload.get("history", [])]
    state.rng.setstate(_decode_rng_state(str(payload["rng_state"])))

    hand = [_card_from_dict(card_payload) for card_payload in payload.get("hand", [])]
    _validate_loaded_hand(state, hand)
    return state, hand


def _validate_loaded_hand(state: GameState, hand: list[Card]) -> None:
    if state.is_over and hand:
        raise ValueError("Save data is invalid: finished campaign cannot have a hand.")
    if not state.is_over and len(hand) != state.config.hand_event_cards + state.config.hand_monster_cards:
        raise ValueError("Save data is invalid: hand must contain exactly 5 cards.")

    event_cards = sum(card.card_type == CARD_EVENT for card in hand)
    monster_cards = sum(card.card_type == CARD_MONSTER for card in hand)
    if hand and (event_cards != 2 or monster_cards != 3):
        raise ValueError("Save data is invalid: hand must contain 2 events and 3 monsters.")


class DesktopGameApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Dungeon Master Roguelike - PC Edition")
        self.geometry("1150x760")
        self.minsize(1040, 700)
        self.configure(bg="#0f172a")

        self.save_path = Path(__file__).resolve().parent / SAVE_FILE_NAME

        self.state: GameState = create_game()
        self.hand: list[Card] = []
        self.selected_indexes: set[int] = set()

        self.status_var = tk.StringVar()
        self.selection_var = tk.StringVar()
        self.party_status_var = tk.StringVar()

        self.hero_widgets: list[dict[str, Any]] = []
        self.card_buttons: list[tk.Button] = []

        self._build_layout()
        self._bind_hotkeys()
        self.new_campaign(show_popup=False)

    def _build_layout(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill=tk.BOTH, expand=True)
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=2)
        root.rowconfigure(0, weight=1)

        left = ttk.Frame(root, padding=(0, 0, 12, 0))
        left.grid(row=0, column=0, sticky="nsew")
        left.columnconfigure(0, weight=1)

        right = ttk.Frame(root)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        title = ttk.Label(
            left,
            text="Dungeon Master Roguelike (PC)",
            font=("Segoe UI", 16, "bold"),
        )
        title.grid(row=0, column=0, sticky="w")

        subtitle = ttk.Label(
            left,
            text="Play as GM: 3 heroes, 5 cards per room (2 events + 3 monsters), play exactly 2.",
            wraplength=360,
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(4, 10))

        controls = ttk.LabelFrame(left, text="Campaign")
        controls.grid(row=2, column=0, sticky="ew")
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)

        ttk.Button(controls, text="New Campaign", command=self.new_campaign).grid(
            row=0, column=0, sticky="ew", padx=(8, 4), pady=8
        )
        ttk.Button(controls, text="Play Selected (Enter)", command=self.play_selected).grid(
            row=0, column=1, sticky="ew", padx=(4, 8), pady=8
        )
        ttk.Button(controls, text="Auto-pick 2", command=self.auto_pick_two).grid(
            row=1, column=0, sticky="ew", padx=(8, 4), pady=(0, 8)
        )
        ttk.Button(controls, text="Save (Ctrl+S)", command=self.save_campaign).grid(
            row=1, column=1, sticky="ew", padx=(4, 8), pady=(0, 8)
        )
        ttk.Button(controls, text="Load (Ctrl+O)", command=self.load_campaign).grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8)
        )

        status_frame = ttk.LabelFrame(left, text="Status")
        status_frame.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        ttk.Label(status_frame, textvariable=self.status_var, wraplength=360).grid(
            row=0, column=0, sticky="w", padx=8, pady=(8, 4)
        )
        ttk.Label(status_frame, textvariable=self.selection_var).grid(
            row=1, column=0, sticky="w", padx=8, pady=(0, 4)
        )
        ttk.Label(status_frame, textvariable=self.party_status_var, wraplength=360).grid(
            row=2, column=0, sticky="w", padx=8, pady=(0, 8)
        )

        heroes_frame = ttk.LabelFrame(left, text="Heroes")
        heroes_frame.grid(row=4, column=0, sticky="ew", pady=(12, 0))
        heroes_frame.columnconfigure(0, weight=1)

        for index in range(3):
            hero_name = tk.StringVar(value=f"Hero {index + 1}")
            hero_hp = tk.StringVar(value="HP")
            row = ttk.Frame(heroes_frame)
            row.grid(row=index, column=0, sticky="ew", padx=8, pady=6)
            row.columnconfigure(0, weight=1)
            ttk.Label(row, textvariable=hero_name, font=("Segoe UI", 10, "bold")).grid(
                row=0, column=0, sticky="w"
            )
            ttk.Label(row, textvariable=hero_hp).grid(row=0, column=1, sticky="e")
            bar = ttk.Progressbar(
                row,
                orient=tk.HORIZONTAL,
                length=280,
                mode="determinate",
                maximum=self.state.config.hero_hp,
            )
            bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(3, 0))
            self.hero_widgets.append(
                {
                    "name_var": hero_name,
                    "hp_var": hero_hp,
                    "bar": bar,
                }
            )

        hand_frame = ttk.LabelFrame(right, text="Hand")
        hand_frame.grid(row=0, column=0, sticky="ew")
        hand_frame.columnconfigure(0, weight=1)

        cards_container = ttk.Frame(hand_frame)
        cards_container.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        cards_container.columnconfigure(0, weight=1)

        for index in range(5):
            button = tk.Button(
                cards_container,
                anchor="w",
                justify="left",
                wraplength=640,
                padx=10,
                pady=10,
                bg="#1f2937",
                fg="#e5e7eb",
                activebackground="#334155",
                activeforeground="#f8fafc",
                relief=tk.RIDGE,
                bd=1,
                command=lambda i=index: self.toggle_card(i),
            )
            button.grid(row=index, column=0, sticky="ew", pady=4)
            self.card_buttons.append(button)

        log_frame = ttk.LabelFrame(right, text="Combat Log")
        log_frame.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            height=16,
            font=("Consolas", 10),
            bg="#020617",
            fg="#dbeafe",
            insertbackground="#dbeafe",
            bd=0,
            highlightthickness=1,
            highlightbackground="#1e293b",
        )
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.log_text.configure(state=tk.DISABLED)

    def _bind_hotkeys(self) -> None:
        self.bind("<Control-s>", lambda _event: self.save_campaign())
        self.bind("<Control-o>", lambda _event: self.load_campaign())
        self.bind("<Control-n>", lambda _event: self.new_campaign())
        self.bind("<Return>", lambda _event: self.play_selected())
        for number in range(1, 6):
            self.bind(str(number), lambda _event, i=number - 1: self.toggle_card(i))

    def new_campaign(self, show_popup: bool = True) -> None:
        self.state = create_game()
        self.hand = draw_hand(self.state)
        self.selected_indexes.clear()
        self._clear_log()
        self._append_log("New campaign started.")
        self._append_log("Select exactly two cards and click 'Play Selected'.")
        self._refresh_ui()
        if show_popup:
            messagebox.showinfo("Campaign", "New campaign started.")

    def toggle_card(self, index: int) -> None:
        if index >= len(self.hand) or self.state.is_over:
            return
        if index in self.selected_indexes:
            self.selected_indexes.remove(index)
        else:
            if len(self.selected_indexes) >= self.state.config.playable_cards:
                self._append_log("You can select only two cards.")
                return
            self.selected_indexes.add(index)
        self._refresh_ui()

    def auto_pick_two(self) -> None:
        if self.state.is_over or len(self.hand) < 2:
            return
        picks = random.sample(range(len(self.hand)), k=self.state.config.playable_cards)
        self.selected_indexes = set(picks)
        self._append_log(f"Auto-picked cards: {picks[0] + 1} and {picks[1] + 1}.")
        self._refresh_ui()

    def play_selected(self) -> None:
        if self.state.is_over:
            return
        if len(self.selected_indexes) != self.state.config.playable_cards:
            self._append_log("Select exactly two cards first.")
            return

        picks = tuple(sorted(self.selected_indexes))
        self.selected_indexes.clear()
        messages = play_selected_cards(self.state, self.hand, picks)
        for message in messages:
            self._append_log(message)

        if not self.state.is_over:
            self.hand = draw_hand(self.state)
            self._append_log("New room generated. Pick two cards.")
        else:
            self.hand = []
            if self.state.campaign_complete and not self.state.party_defeated:
                self._append_log(f"Victory! Final score: {self.state.score}.")
                messagebox.showinfo("Campaign complete", f"You win! Score: {self.state.score}")
            else:
                self._append_log(f"Defeat. Final score: {self.state.score}.")
                messagebox.showwarning("Campaign failed", f"All heroes are down. Score: {self.state.score}")

        self._refresh_ui()

    def save_campaign(self) -> None:
        payload = serialize_campaign(self.state, self.hand)
        self.save_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self._append_log(f"Campaign saved to {self.save_path.name}.")

    def load_campaign(self) -> None:
        if not self.save_path.exists():
            messagebox.showerror("Load failed", f"File not found: {self.save_path.name}")
            return
        try:
            payload = json.loads(self.save_path.read_text(encoding="utf-8"))
            state, hand = deserialize_campaign(payload)
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Load failed", str(error))
            return

        self.state = state
        self.hand = hand
        self.selected_indexes.clear()
        self._append_log("Campaign loaded from disk.")
        self._refresh_ui()

    def _refresh_ui(self) -> None:
        self.status_var.set(format_status(self.state))
        self.selection_var.set(
            f"Selected cards: {len(self.selected_indexes)}/{self.state.config.playable_cards}"
        )
        self.party_status_var.set(
            "Party: " + " | ".join(f"{hero.name}: {hero.hp} HP" for hero in self.state.party)
        )

        for hero, widget in zip(self.state.party, self.hero_widgets):
            widget["name_var"].set(hero.name)
            widget["hp_var"].set(f"{hero.hp}/{self.state.config.hero_hp} HP")
            widget["bar"]["maximum"] = self.state.config.hero_hp
            widget["bar"]["value"] = max(hero.hp, 0)

        for index, button in enumerate(self.card_buttons):
            if index < len(self.hand):
                card = self.hand[index]
                button.configure(
                    state=tk.NORMAL if not self.state.is_over else tk.DISABLED,
                    text=self._card_label(index, card),
                    bg=self._card_background(index, card.card_type),
                )
            else:
                button.configure(
                    state=tk.DISABLED,
                    text=f"{index + 1}. [empty]\nNo card available.",
                    bg="#1f2937",
                )

    def _card_label(self, index: int, card: Card) -> str:
        if card.card_type == CARD_EVENT:
            meta = f"effect={card.effect_id}, potency={card.potency}"
        else:
            meta = f"danger={card.danger}, reward={card.reward}"
        return (
            f"{index + 1}. [{card.card_type.upper()}] {card.name}\n"
            f"{card.description}\n"
            f"{meta}"
        )

    def _card_background(self, index: int, card_type: str) -> str:
        if index in self.selected_indexes:
            return "#0f766e"
        if card_type == CARD_EVENT:
            return "#0c4a6e"
        return "#7f1d1d"

    def _append_log(self, line: str) -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{line}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _clear_log(self) -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)


def run_desktop_game() -> None:
    app = DesktopGameApp()
    app.mainloop()


if __name__ == "__main__":
    run_desktop_game()
