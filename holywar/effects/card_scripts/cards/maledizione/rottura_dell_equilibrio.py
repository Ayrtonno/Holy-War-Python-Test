from __future__ import annotations

CARD_NAME = "Rottura dell'Equilibrio"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {"effect": {"action": "inflict_sin", "amount": 3, "target_player": "opponent"}},
        {"effect": {"action": "inflict_sin", "amount": 1, "target_player": "me"}},
    ],
}
