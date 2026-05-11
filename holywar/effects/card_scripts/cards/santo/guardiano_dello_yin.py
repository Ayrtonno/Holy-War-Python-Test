from __future__ import annotations

CARD_NAME = "Guardiano dello Yin"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_inspiration_gained",
                "frequency": "each_time",
                "condition": {"payload_target_player": "opponent"},
            },
            "target": {"type": "source_card"},
            "effect": {"action": "remove_sin", "amount": 1, "target_player": "me"},
        }
    ],
    "on_play_actions": [],
}
