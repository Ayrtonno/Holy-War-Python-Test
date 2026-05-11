from __future__ import annotations

CARD_NAME = "Guardiana dello Yang"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_sin_removed",
                "frequency": "each_time",
                "condition": {"payload_target_player": "me"},
            },
            "target": {"type": "source_card"},
            "effect": {"action": "inflict_sin", "amount": 1, "target_player": "opponent"},
        }
    ],
    "on_play_actions": [],
}
