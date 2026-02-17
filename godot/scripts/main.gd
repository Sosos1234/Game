extends Control

const CARD_EVENT := "event"
const CARD_MONSTER := "monster"

const HERO_NAMES := ["Warrior", "Mage", "Rogue"]
const HERO_HP := 14
const HERO_POWER := 2
const MAX_ROOMS := 6
const PLAYABLE_CARDS := 2
const HAND_EVENT_CARDS := 2
const HAND_MONSTER_CARDS := 3

var event_templates: Array[Dictionary] = [
	{
		"name": "Campfire Respite",
		"effect_id": "campfire",
		"description": "All living heroes recover 2 HP.",
		"potency": 2,
	},
	{
		"name": "Ceiling Trap",
		"effect_id": "trap",
		"description": "All living heroes take 2 damage.",
		"potency": 2,
	},
	{
		"name": "Hidden Cache",
		"effect_id": "cache",
		"description": "One random living hero recovers 4 HP.",
		"potency": 4,
	},
	{
		"name": "Dark Omen",
		"effect_id": "omen",
		"description": "One random living hero takes 4 damage.",
		"potency": 4,
	},
]

var monster_templates: Array[Dictionary] = [
	{
		"name": "Goblin Ambush",
		"description": "Quick raiders strike from both sides.",
		"base_danger": 1,
		"reward": 14,
	},
	{
		"name": "Skeleton Knight",
		"description": "A disciplined undead duelist blocks the corridor.",
		"base_danger": 2,
		"reward": 20,
	},
	{
		"name": "Ogre Brute",
		"description": "A heavy hitter with room-wide threat.",
		"base_danger": 3,
		"reward": 26,
	},
	{
		"name": "Cult Warlock",
		"description": "Ritual magic weakens the party defense.",
		"base_danger": 2,
		"reward": 22,
	},
	{
		"name": "Cave Stalker",
		"description": "A silent predator from the shadows.",
		"base_danger": 1,
		"reward": 16,
	},
]

var rng := RandomNumberGenerator.new()

var room: int = 1
var score: int = 0
var party: Array[Dictionary] = []
var hand: Array[Dictionary] = []
var selected_indexes: Array[int] = []

var status_label: Label
var party_label: Label
var selection_label: Label
var hand_container: VBoxContainer
var play_button: Button
var log_output: RichTextLabel


func _ready() -> void:
	rng.randomize()
	_build_ui()
	_new_campaign()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_1:
				_toggle_card_by_hotkey(0)
			KEY_2:
				_toggle_card_by_hotkey(1)
			KEY_3:
				_toggle_card_by_hotkey(2)
			KEY_4:
				_toggle_card_by_hotkey(3)
			KEY_5:
				_toggle_card_by_hotkey(4)
			KEY_ENTER, KEY_KP_ENTER:
				_play_selected()


func _build_ui() -> void:
	var root := MarginContainer.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_theme_constant_override("margin_left", 14)
	root.add_theme_constant_override("margin_top", 14)
	root.add_theme_constant_override("margin_right", 14)
	root.add_theme_constant_override("margin_bottom", 14)
	add_child(root)

	var split := HSplitContainer.new()
	split.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	split.split_offset = 380
	root.add_child(split)

	var left_column := VBoxContainer.new()
	left_column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	left_column.size_flags_vertical = Control.SIZE_EXPAND_FILL
	left_column.add_theme_constant_override("separation", 10)
	split.add_child(left_column)

	var title := Label.new()
	title.text = "Dungeon Master Roguelike - Godot"
	title.add_theme_font_size_override("font_size", 24)
	left_column.add_child(title)

	var subtitle := Label.new()
	subtitle.text = "GM campaign: 3 heroes, 5 cards (2 events + 3 monsters), play exactly 2."
	subtitle.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	left_column.add_child(subtitle)

	status_label = Label.new()
	status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	left_column.add_child(status_label)

	selection_label = Label.new()
	left_column.add_child(selection_label)

	party_label = Label.new()
	party_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	left_column.add_child(party_label)

	var controls_row := HBoxContainer.new()
	left_column.add_child(controls_row)

	var new_button := Button.new()
	new_button.text = "New Campaign"
	new_button.pressed.connect(_new_campaign)
	controls_row.add_child(new_button)

	play_button = Button.new()
	play_button.text = "Play Selected (Enter)"
	play_button.pressed.connect(_play_selected)
	controls_row.add_child(play_button)

	var info := Label.new()
	info.text = "Hotkeys: 1..5 select cards, Enter plays turn."
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	left_column.add_child(info)

	log_output = RichTextLabel.new()
	log_output.fit_content = false
	log_output.scroll_following = true
	log_output.bbcode_enabled = false
	log_output.size_flags_vertical = Control.SIZE_EXPAND_FILL
	left_column.add_child(log_output)

	var right_column := VBoxContainer.new()
	right_column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right_column.size_flags_vertical = Control.SIZE_EXPAND_FILL
	right_column.add_theme_constant_override("separation", 8)
	split.add_child(right_column)

	var hand_title := Label.new()
	hand_title.text = "Hand"
	hand_title.add_theme_font_size_override("font_size", 20)
	right_column.add_child(hand_title)

	var hand_hint := Label.new()
	hand_hint.text = "Select exactly two cards and press Play Selected."
	hand_hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	right_column.add_child(hand_hint)

	var hand_scroll := ScrollContainer.new()
	hand_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	right_column.add_child(hand_scroll)

	hand_container = VBoxContainer.new()
	hand_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hand_container.add_theme_constant_override("separation", 6)
	hand_scroll.add_child(hand_container)


func _new_campaign() -> void:
	room = 1
	score = 0
	selected_indexes.clear()
	party.clear()
	for hero_name in HERO_NAMES:
		party.append(
			{
				"name": hero_name,
				"hp": HERO_HP,
				"power": HERO_POWER,
			}
		)
	hand = _draw_hand()
	log_output.clear()
	_append_log("New campaign started.")
	_append_log("Choose exactly two cards and press Play Selected.")
	_refresh_ui()


func _draw_hand() -> Array[Dictionary]:
	var cards: Array[Dictionary] = []
	var events := _sample_unique(event_templates, HAND_EVENT_CARDS)
	var monsters := _sample_unique(monster_templates, HAND_MONSTER_CARDS)

	for template in events:
		cards.append(
			{
				"name": template["name"],
				"card_type": CARD_EVENT,
				"description": template["description"],
				"effect_id": template["effect_id"],
				"potency": template["potency"],
				"danger": 0,
				"reward": 0,
			}
		)

	for template in monsters:
		var danger := int(template["base_danger"]) + int((room - 1) / 2)
		var reward := int(template["reward"]) + (room - 1) * 3
		cards.append(
			{
				"name": template["name"],
				"card_type": CARD_MONSTER,
				"description": template["description"],
				"effect_id": "",
				"potency": 0,
				"danger": danger,
				"reward": reward,
			}
		)

	_shuffle(cards)
	return cards


func _sample_unique(source: Array[Dictionary], count: int) -> Array[Dictionary]:
	var pool: Array[Dictionary] = source.duplicate(true)
	_shuffle(pool)
	var result: Array[Dictionary] = []
	var limit := mini(count, pool.size())
	for i in range(limit):
		result.append(pool[i].duplicate(true))
	return result


func _shuffle(items: Array) -> void:
	for i in range(items.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var temp = items[i]
		items[i] = items[j]
		items[j] = temp


func _toggle_card_by_hotkey(index: int) -> void:
	if _is_game_over():
		return
	if index >= hand.size():
		return
	if selected_indexes.has(index):
		selected_indexes.erase(index)
	else:
		if selected_indexes.size() >= PLAYABLE_CARDS:
			_append_log("You can pick only two cards.")
			return
		selected_indexes.append(index)
	_refresh_ui()


func _on_card_toggled(index: int, pressed: bool) -> void:
	if _is_game_over():
		return
	if pressed:
		if selected_indexes.has(index):
			return
		if selected_indexes.size() >= PLAYABLE_CARDS:
			_append_log("You can pick only two cards.")
			_refresh_ui()
			return
		selected_indexes.append(index)
	else:
		selected_indexes.erase(index)
	_refresh_ui()


func _play_selected() -> void:
	if _is_game_over():
		return
	if selected_indexes.size() != PLAYABLE_CARDS:
		_append_log("Select exactly two cards first.")
		return

	var picks: Array[int] = selected_indexes.duplicate()
	picks.sort()
	selected_indexes.clear()

	var messages := _resolve_turn(picks)
	for line in messages:
		_append_log(line)

	if _is_game_over():
		hand.clear()
		if _campaign_complete() and not _party_defeated():
			_append_log("Victory! Final score: %d" % score)
		else:
			_append_log("Defeat. Final score: %d" % score)
	else:
		hand = _draw_hand()
		_append_log("A new room appears. Choose two cards.")

	_refresh_ui()


func _resolve_turn(picks: Array[int]) -> Array[String]:
	var messages: Array[String] = []
	for index in picks:
		var card: Dictionary = hand[index]
		var card_type: String = str(card["card_type"])
		var result := _resolve_card(card)
		messages.append("%s - %s: %s" % [card_type.to_upper(), card["name"], result])
		if _party_defeated():
			messages.append("All heroes are down. The campaign fails here.")
			break

	if not _party_defeated():
		room += 1
		if _campaign_complete():
			var bonus := _survivors_count() * 25
			score += bonus
			messages.append("Campaign complete. Survivor bonus: +%d score." % bonus)

	return messages


func _resolve_card(card: Dictionary) -> String:
	var card_type: String = str(card["card_type"])
	if card_type == CARD_EVENT:
		return _apply_event(card)
	if card_type == CARD_MONSTER:
		return _apply_monster(card)
	return "Unknown card type."


func _apply_event(card: Dictionary) -> String:
	var living := _living_indices()
	if living.is_empty():
		return "No heroes are alive to resolve this event."

	var effect_id: String = str(card["effect_id"])
	var potency := int(card["potency"])

	if effect_id == "campfire":
		for hero_index in living:
			_change_hero_hp(hero_index, potency)
		score += 8
		return "The party regroups and recovers health."

	if effect_id == "trap":
		for hero_index in living:
			_change_hero_hp(hero_index, -potency)
		score -= 4
		return "A trap goes off and injures every hero."

	var target_index: int = living[rng.randi_range(0, living.size() - 1)]
	if effect_id == "cache":
		_change_hero_hp(target_index, potency)
		score += 10
		return "%s finds supplies and recovers health." % party[target_index]["name"]

	_change_hero_hp(target_index, -potency)
	score += 2
	return "%s suffers from a dark omen." % party[target_index]["name"]


func _apply_monster(card: Dictionary) -> String:
	var living := _living_indices()
	if living.is_empty():
		return "No heroes remain to face monsters."

	var party_roll := 0
	for hero_index in living:
		party_roll += rng.randi_range(1, 6) + int(party[hero_index]["power"])

	var danger := int(card["danger"])
	var monster_roll := rng.randi_range(1, 6) + danger * 3 + maxi(0, room - 1)

	if party_roll >= monster_roll:
		score += int(card["reward"])
		var margin := party_roll - monster_roll
		if margin <= 2:
			var target_index: int = living[rng.randi_range(0, living.size() - 1)]
			_change_hero_hp(target_index, -1)
			return "The party defeats %s, but %s loses 1 HP." % [card["name"], party[target_index]["name"]]
		return "The party defeats %s." % card["name"]

	var damage := maxi(1, danger)
	for hero_index in living:
		_change_hero_hp(hero_index, -damage)
	score -= 6 * danger
	return "%s overwhelms the party. Every hero loses %d HP." % [card["name"], damage]


func _change_hero_hp(hero_index: int, delta: int) -> void:
	var current := int(party[hero_index]["hp"])
	party[hero_index]["hp"] = clampi(current + delta, 0, HERO_HP)


func _living_indices() -> Array[int]:
	var indexes: Array[int] = []
	for i in range(party.size()):
		if int(party[i]["hp"]) > 0:
			indexes.append(i)
	return indexes


func _survivors_count() -> int:
	return _living_indices().size()


func _party_defeated() -> bool:
	return _survivors_count() == 0


func _campaign_complete() -> bool:
	return room > MAX_ROOMS


func _is_game_over() -> bool:
	return _party_defeated() or _campaign_complete()


func _refresh_ui() -> void:
	status_label.text = "Room: %d/%d | Survivors: %d/3 | Score: %d" % [
		mini(room, MAX_ROOMS),
		MAX_ROOMS,
		_survivors_count(),
		score,
	]
	selection_label.text = "Selected cards: %d/%d" % [selected_indexes.size(), PLAYABLE_CARDS]
	party_label.text = "Party: %s" % _party_line()
	play_button.disabled = selected_indexes.size() != PLAYABLE_CARDS or _is_game_over()
	_rebuild_hand_buttons()


func _party_line() -> String:
	var chunks: Array[String] = []
	for hero in party:
		chunks.append("%s:%dHP" % [hero["name"], hero["hp"]])
	return " | ".join(chunks)


func _rebuild_hand_buttons() -> void:
	for child in hand_container.get_children():
		child.queue_free()

	if hand.is_empty():
		var no_cards := Label.new()
		no_cards.text = "No cards available. Start a new campaign."
		no_cards.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		hand_container.add_child(no_cards)
		return

	for i in range(hand.size()):
		var card: Dictionary = hand[i]
		var button := Button.new()
		button.toggle_mode = true
		button.alignment = HORIZONTAL_ALIGNMENT_LEFT
		button.text = _card_label(i, card)
		button.custom_minimum_size = Vector2(0, 82)
		button.disabled = _is_game_over()
		button.button_pressed = selected_indexes.has(i)

		var index := i
		button.toggled.connect(func(pressed: bool) -> void:
			_on_card_toggled(index, pressed)
		)
		hand_container.add_child(button)


func _card_label(index: int, card: Dictionary) -> String:
	var meta: String
	if str(card["card_type"]) == CARD_EVENT:
		meta = "effect=%s, potency=%d" % [card["effect_id"], card["potency"]]
	else:
		meta = "danger=%d, reward=%d" % [card["danger"], card["reward"]]
	return "%d. [%s] %s\n%s\n%s" % [
		index + 1,
		str(card["card_type"]).to_upper(),
		card["name"],
		card["description"],
		meta,
	]


func _append_log(line: String) -> void:
	log_output.append_text(line + "\n")
	log_output.scroll_to_line(maxi(log_output.get_line_count() - 1, 0))
