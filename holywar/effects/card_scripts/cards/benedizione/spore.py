from __future__ import annotations

CARD_NAME = 'Spore'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "effect": {
                "action": "mill_cards",
                "amount": 1,
                "target_player": "opponent",
            }
        }
    ],
}
