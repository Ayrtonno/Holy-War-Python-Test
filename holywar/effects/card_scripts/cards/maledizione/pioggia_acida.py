from __future__ import annotations

CARD_NAME = 'Pioggia Acida'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "all_saints_on_field",
                "card_filter": {
                    "card_type_in": ["santo"],
                },
            },
            "effect": {
                "action": "decrease_faith",
                "amount": 2,
            },
        },
    ],
}
