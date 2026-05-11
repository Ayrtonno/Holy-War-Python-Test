from __future__ import annotations

CARD_NAME = "Riflusso del Karma"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {"effect": {"action": "set_pending_sin_mirror_once", "target_player": "me", "amount": 1}},
    ],
}
