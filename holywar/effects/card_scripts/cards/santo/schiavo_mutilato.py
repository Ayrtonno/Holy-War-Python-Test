from __future__ import annotations

CARD_NAME = """Schiavo Mutilato"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_this_card_kills_in_battle",
                "frequency": "each_turn",
            },
            "target": {"type": "event_card"},
            "effect": {"action": "increase_faith", "amount": 2},
        },
        {
            "trigger": {
                "event": "on_this_card_kills_in_battle",
                "frequency": "each_turn",
            },
            "target": {"type": "event_card"},
            "effect": {"action": "increase_strength", "amount": 2},
        },
    ],
    "on_play_actions": [],
}
