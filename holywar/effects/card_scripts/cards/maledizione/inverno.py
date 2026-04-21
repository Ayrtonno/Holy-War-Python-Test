from __future__ import annotations

CARD_NAME = "Inverno"

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
                "zone": "field",
                "owner": "any",
                "card_filter": {
                    "crosses_lte": 8,
                },
                "min_targets": 1,
                "max_targets": 3,
            },
            "effect": {
                "action": "excommunicate_card",
            },
        },
        {
            "target": {
                "type": "source_card",
            },
            "effect": {
                "action": "excommunicate_card",
            },
        },
    ],
}