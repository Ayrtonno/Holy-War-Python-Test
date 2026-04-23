from __future__ import annotations

CARD_NAME = 'Giorno 2: Cielo Terrestre'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {"type": "all_saints_on_field"},
            "effect": {"action": "prevent_specific_card_from_attacking", "amount": 1},
        },
    ],
}
