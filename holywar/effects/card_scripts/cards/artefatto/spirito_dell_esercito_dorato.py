from __future__ import annotations

CARD_NAME = "Spirito dell'Esercito Dorato"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "triggered_effects": [
        {
            "trigger": {"event": "on_my_turn_start", "frequency": "each_turn"},
            "target": {"type": "none"},
            "effect": {"action": "pay_sin_or_destroy_self", "amount": 5},
        }
    ],
    "on_activate_actions": [
        {
            "target": {"type": "none"},
            "effect": {
                "action": "summon_token",
                "card_name": "Spirito Vacuo",
            },
        }
    ],
    "on_play_actions": [],
}