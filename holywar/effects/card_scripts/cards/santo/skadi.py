from __future__ import annotations

CARD_NAME = """Skadi"""

SCRIPT = {
    "on_play_mode": "noop",
    "play_targeting": "none",
    "on_enter_mode": "scripted",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "on_play_actions": [],
    "on_enter_actions": [
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "owner": "opponent",
                "zones": ["field"],
                "card_filter": {"card_type_in": ["santo"], "strength_gte": 5},
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "target": {
                "type": "selected_target",
                "owner": "opponent",
                "zones": ["field"],
                "card_filter": {"card_type_in": ["santo"], "strength_gte": 5},
            },
            "effect": {"action": "decrease_strength", "amount": 3},
        },
    ],
}
