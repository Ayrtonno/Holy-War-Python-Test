from __future__ import annotations

CARD_NAME = 'Giorno 1: Cieli e Terra'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {"type": "source_card"},
            "effect": {"action": "add_temporary_inspiration", "amount": 2, "target_player": "me"},
        },
    ],
}
