from __future__ import annotations

CARD_NAME = "Piaga: Morte dei Primogeniti"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "guided",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "selected_target",
                "zone": "field",
                "owner": "opponent",
                "card_filter": {"card_type_in": ["santo", "token"]},
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "decrease_faith", "amount": 6},
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "inflict_sin", "amount": 4, "target_player": "opponent"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {
                "action": "optional_recover_matching_then_shuffle",
                "from_zone": "graveyard",
                "to_zone": "hand",
                "card_name": "Piaga",
                "amount": 1,
                "shuffle_after": False,
            },
        },
    ],
}

