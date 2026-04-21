from __future__ import annotations

CARD_NAME = "Diboscamento"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "guided",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "selected_targets",
                "zone": "deck",
                "owner": "me",
                "card_filter": {
                    "name_contains": "Albero",
                },
                "min_targets": 1,
                "max_targets": 3,
            },
            "effect": {
                "action": "send_to_graveyard",
            },
        },
    ],
}