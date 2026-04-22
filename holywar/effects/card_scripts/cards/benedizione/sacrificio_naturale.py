from __future__ import annotations

CARD_NAME = 'Sacrificio Naturale'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "play_requirements": {
        "not": {
            "controller_has_cards": {
                "owner": "opponent",
                "zone": "defense",
                "min_count": 1,
                "card_filter": {"card_type_in": ["santo", "token"]},
            }
        }
    },
    "on_play_actions": [
        {
            "target": {"type": "source_card"},
            "effect": {
                "action": "summon_generated_token",
                "card_name": "Token Sacrificale",
                "amount": 3,
                "owner": "opponent",
                "zone": "defense",
            },
        }
    ],
}
