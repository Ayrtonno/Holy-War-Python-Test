from __future__ import annotations

CARD_NAME = "Patto dei Reishi"

HAS_3_BAXIAN = {
    "controller_has_cards": {
        "zones": ["field"],
        "owner": "me",
        "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
        "min_count": 3,
    }
}

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "auto",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "condition": {"not": HAS_3_BAXIAN},
            "target": {"type": "selected_target"},
            "effect": {"action": "increase_strength", "amount": 2},
        },
        {
            "condition": {"not": HAS_3_BAXIAN},
            "target": {"type": "selected_target"},
            "effect": {"action": "increase_faith", "amount": 2},
        },
        {
            "condition": HAS_3_BAXIAN,
            "target": {"type": "selected_target"},
            "effect": {"action": "increase_strength", "amount": 4},
        },
        {
            "condition": HAS_3_BAXIAN,
            "target": {"type": "selected_target"},
            "effect": {"action": "increase_faith", "amount": 4},
        },
    ],
}
