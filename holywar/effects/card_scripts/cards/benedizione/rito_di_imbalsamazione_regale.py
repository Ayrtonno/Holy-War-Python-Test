from __future__ import annotations

CARD_NAME = "Rito di Imbalsamazione Regale"

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
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {
                    "card_type_in": ["santo"],
                    "crosses_lte": 6,
                },
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "move_to_hand"},
        },
        {
            "target": {
                "type": "selected_target",
                "zone": "hand",
                "owner": "me",
                "min_targets": 0,
                "max_targets": 1,
            },
            "effect": {"action": "send_to_graveyard"},
        },
    ],
}

