from __future__ import annotations

CARD_NAME = "Cura"
#
SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "select_card",
                "zone": "field",
                "owner": "any",
                "card_filter": {
                    "card_type_in": ["santo"],
                },
            },
            "effect": {
                "action": "increase_faith",
                "amount": 5,
            },
        }
    ],
}