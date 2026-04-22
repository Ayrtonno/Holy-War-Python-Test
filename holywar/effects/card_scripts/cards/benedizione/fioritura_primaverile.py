from __future__ import annotations

CARD_NAME = 'Fioritura Primaverile'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "owner": "me",
                "zone": "field",
                "card_filter": {
                    "card_type_in": ["santo", "token"],
                    "expansion_in": ["ANI-1"],
                },
            },
            "effect": {"action": "increase_faith", "amount": 2},
        },
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "owner": "me",
                "zone": "field",
                "card_filter": {
                    "card_type_in": ["santo", "token"],
                    "expansion_in": ["ANI-1"],
                },
            },
            "effect": {"action": "increase_strength", "amount": 2},
        },
    ],
}
