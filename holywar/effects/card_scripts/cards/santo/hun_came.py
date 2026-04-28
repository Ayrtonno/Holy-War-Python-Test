from __future__ import annotations

CARD_NAME = """Hun-Came"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "counted_bonuses": [
        {
            "context": "strength",
            "group": "hun_came_grave_scaling",
            "stacking": "max",
            "threshold": 5,
            "amount_mode": "per_count_div_floor",
            "divisor": 5,
            "amount": 2,
            "requirement": {
                "owner": "me",
                "zone": "graveyard",
            },
        }
    ],
    "triggered_effects": [],
    "on_play_actions": [],
}
