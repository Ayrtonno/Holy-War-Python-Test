from __future__ import annotations

CARD_NAME = "Laozi, Custode del Vuoto"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {"effect": {"action": "remove_sin", "amount": 2, "target_player": "me"}},
        {"effect": {"action": "inflict_sin", "amount": 2, "target_player": "opponent"}},
    ],
}
