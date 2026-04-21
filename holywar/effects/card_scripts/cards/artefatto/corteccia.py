from __future__ import annotations

CARD_NAME = "Corteccia"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_enter_field",
                "frequency": "each_time",
                "condition": {"event_card_owner": "me"},
            },
            "target": {
                "type": "event_card",
                "card_filter": {
                    "name_contains": "Albero",
                    "card_type_in": ["santo", "token"],
                },
            },
            "effect": {
                "action": "increase_faith",
                "amount": 5,
                "duration": "until_source_leaves",
            },
        }
    ],
    "on_play_actions": [
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {
                    "name_contains": "albero",
                    "card_type_in": ["santo", "token"],
                },
            },
            "effect": {
                "action": "increase_faith",
                "amount": 5,
                "duration": "until_source_leaves",
            },
        }
    ],
}
