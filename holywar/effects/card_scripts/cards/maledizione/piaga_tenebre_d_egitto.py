from __future__ import annotations

CARD_NAME = "Piaga: Tenebre d'Egitto"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "guided",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {"type": "source_card"},
            "effect": {"action": "set_next_turn_draw_override", "amount": 2, "target_player": "opponent"},
        },
        {
            "target": {
                "type": "selected_target",
                "zone": "deck",
                "owner": "me",
                "card_filter": {"name_contains": "Piaga"},
                "min_targets": 0,
                "max_targets": 1,
            },
            "effect": {"action": "move_to_hand"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "shuffle_deck", "target_player": "me"},
        },
    ],
}

