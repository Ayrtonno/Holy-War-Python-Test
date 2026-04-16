from __future__ import annotations

CARD_NAME = """Golem di Pietra"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_this_card_kills_in_battle"
            },
            "target": {"type": "source_card"},
            "effect": {
                "action": "increase_faith",
                "amount": 4
            },
        }
    ],
    "on_play_actions": [],
}
