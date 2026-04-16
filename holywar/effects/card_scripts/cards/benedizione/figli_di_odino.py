from __future__ import annotations

CARD_NAME = """Figli di Odino"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "own_saint",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "condition": {
                "all_of": [
                    {"controller_has_saint_with_name": "Odino"},
                    {"controller_has_saint_with_name": "Thor"},
                ]
            },
            "target": {"type": "selected_target"},
            "effect": {"action": "increase_strength", "amount": 6},
        },
        {
            "condition": {
                "all_of": [
                    {"controller_has_saint_with_name": "Odino"},
                    {"not": {"controller_has_saint_with_name": "Thor"}},
                ]
            },
            "target": {"type": "selected_target"},
            "effect": {"action": "increase_strength", "amount": 6},
        },
        {
            "condition": {"not": {"controller_has_saint_with_name": "Odino"}},
            "target": {"type": "selected_target"},
            "effect": {"action": "increase_strength", "amount": 3},
        },
        {
            "condition": {
                "all_of": [
                    {"controller_has_saint_with_name": "Odino"},
                    {"controller_has_saint_with_name": "Thor"},
                ]
            },
            "target": {"type": "source_card"},
            "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"},
        },
    ],
}

