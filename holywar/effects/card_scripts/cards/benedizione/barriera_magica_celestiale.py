from __future__ import annotations

CARD_NAME = 'Barriera Magica Celestiale'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "effect": {
                "action": "add_inspiration",
                "amount": 2,
                "target_player": "me",
            }
        }
    ],
}
