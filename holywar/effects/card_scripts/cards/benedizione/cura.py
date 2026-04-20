from __future__ import annotations

CARD_NAME = "Cura"
#
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
                "owner": "me",
                "card_filter": {
                    "card_type_in": ["santo"],
                },
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {
                "action": "increase_faith",
                "amount": 5,
            },
        }
    ],
}