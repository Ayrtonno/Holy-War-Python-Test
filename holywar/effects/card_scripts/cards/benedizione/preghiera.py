from __future__ import annotations

CARD_NAME = "Preghiera"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "effect": {
                "action": "remove_sin",
                "amount": 5,
                "target_player": "me",
            },
        },
    ],
}