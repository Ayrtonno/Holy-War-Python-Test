from __future__ import annotations

CARD_NAME = """Tempesta di Asgard"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "condition": {"controller_has_saint_with_name": "Thor"},
            "target": {
                "type": "all_saints_on_field",
                "card_filter": {"card_type_in": ["santo", "token"]},
            },
            "effect": {"action": "decrease_faith", "amount": 4},
        },
        {
            "condition": {"not": {"controller_has_saint_with_name": "Thor"}},
            "target": {
                "type": "all_saints_on_field",
                "card_filter": {"card_type_in": ["santo", "token"]},
            },
            "effect": {"action": "decrease_faith", "amount": 2},
        },
    ],
}
