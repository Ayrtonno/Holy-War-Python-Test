from __future__ import annotations

CARD_NAME = """Fuoco"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_turn_end", "frequency": "each_turn"},
            "target": {
                "type": "all_saints_on_field",
                "card_filter": {"card_type_in": ["santo"], "crosses_gte": 4},
            },
            "effect": {"action": "decrease_faith", "amount": 2},
        }
    ],
    "on_play_actions": [],
}
