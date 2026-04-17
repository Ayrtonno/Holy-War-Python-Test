from __future__ import annotations

CARD_NAME = """Xibalba"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_summoned_from_graveyard",
                "frequency": "each_time",
                "condition": {"event_card_type_in": ["santo"]},
            },
            "target": {"type": "event_card"},
            "effect": {"action": "increase_faith", "amount": 5},
        },
        {
            "trigger": {
                "event": "on_summoned_from_graveyard",
                "frequency": "each_time",
                "condition": {"event_card_type_in": ["santo"]},
            },
            "target": {"type": "event_card"},
            "effect": {"action": "increase_strength", "amount": 5},
        },
        {
            "trigger": {
                "event": "on_summoned_from_graveyard",
                "frequency": "each_time",
                "condition": {"event_card_type_in": ["santo"]},
            },
            "target": {"type": "none"},
            "effect": {"action": "remove_sin", "amount": 3, "target_player": "me"},
        },
    ],
    "on_play_actions": [],
}