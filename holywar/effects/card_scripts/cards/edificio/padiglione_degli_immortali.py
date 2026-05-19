from __future__ import annotations

CARD_NAME = "Padiglione degli Immortali"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [],
    "counted_bonuses": [
        {
            "context": "strength",
            "amount_mode": "per_count_div_floor",
            "divisor": 1,
            "amount": 3,
            "stacking": "sum",
            "target_card_type_in": ["santo"],
            "requirement": {
                "zones": ["field"],
                "owner": "me",
                "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
            },
        },
        {
            "context": "faith",
            "amount_mode": "per_count_div_floor",
            "divisor": 1,
            "amount": 3,
            "stacking": "sum",
            "target_card_type_in": ["santo"],
            "requirement": {
                "zones": ["graveyard"],
                "owner": "me",
                "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
            },
        },
    ],
}
