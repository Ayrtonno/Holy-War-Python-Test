from __future__ import annotations

CARD_NAME = "Biblioteca Apostolica"

SEARCH_FILTER = {
    "card_type_in": ["benedizione", "maledizione"],
}

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "activate_once_per_turn": True,
    "play_targeting": "none",
    "activate_targeting": "guided",
    "triggered_effects": [
        {
            "trigger": {"event": "on_blessing_played", "frequency": "each_turn"},
            "target": {"type": "source_card"},
            "effect": {"action": "campana_add_counter"},
        },
        {
            "trigger": {"event": "on_curse_played", "frequency": "each_turn"},
            "target": {"type": "source_card"},
            "effect": {"action": "campana_add_counter"},
        },
    ],
    "on_play_actions": [
        {"effect": {"action": "draw_cards", "amount": 0, "target_player": "me"}},
    ],
    "on_activate_actions": [
        {
            "condition": {"source_counter_gte": 3},
            "target": {
                "type": "selected_target",
                "zone": "deck",
                "owner": "me",
                "card_filter": SEARCH_FILTER,
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "move_to_hand"},
        },
        {
            "condition": {"source_counter_gte": 3},
            "target": {"type": "source_card"},
            "effect": {"action": "campana_remove_counter", "amount": 3},
        },
        {
            "condition": {"source_counter_gte": 3},
            "target": {"type": "source_card"},
            "effect": {"action": "shuffle_deck", "target_player": "me"},
        },
    ],
}
