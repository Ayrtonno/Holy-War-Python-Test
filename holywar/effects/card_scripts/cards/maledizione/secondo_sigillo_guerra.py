from __future__ import annotations

CARD_NAME = 'Secondo Sigillo: Guerra'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "effect": {
                "action": "inflict_sin",
                "amount": 4,
                "target_player": "opponent",
            }
        }
    ],
}
