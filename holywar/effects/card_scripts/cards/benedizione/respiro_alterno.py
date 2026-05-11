from __future__ import annotations

CARD_NAME = "Respiro Alterno"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"},
        },
        {
            "effect": {"action": "mill_cards", "amount": 1, "target_player": "opponent"},
        },
    ],
}
