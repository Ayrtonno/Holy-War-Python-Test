from __future__ import annotations

CARD_NAME = "He Xian'gu"

HAS_2_BAXIAN_GRAVE = {
    "controller_has_cards": {
        "zones": ["graveyard"],
        "owner": "me",
        "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
        "min_count": 2,
    }
}

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "condition": HAS_2_BAXIAN_GRAVE,
            "effect": {"action": "remove_sin", "amount": 8, "target_player": "me"},
        },
        {
            "condition": {"not": HAS_2_BAXIAN_GRAVE},
            "effect": {"action": "remove_sin", "amount": 4, "target_player": "me"},
        },
    ],
}
