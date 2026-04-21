from __future__ import annotations

CARD_NAME = """Schiavi"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_this_card_receives_damage",
                "frequency": "each_time",
                "condition": {
                    "all_of": [
                        {"target_current_faith_gte": 1},
                        {"target_is_damaged": True},
                    ]
                },
            },
            "target": {"type": "source_card"},
            "effect": {"action": "increase_faith", "amount": 2},
        }
    ],
    "on_play_actions": [],
}
