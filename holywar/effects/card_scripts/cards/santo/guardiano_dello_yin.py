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
                "event": "on_card_drawn",
                "frequency": "each_time",
                "condition": {"event_card_owner": "opponent"},
            },
            "target": {"type": "source_card"},
            "effect": {"action": "remove_sin", "amount": 1, "target_player": "me"},
        }
    ],
    "on_play_actions": [],
}
