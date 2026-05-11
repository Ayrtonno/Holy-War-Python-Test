from __future__ import annotations

CARD_NAME = "Sigillo dei Mortali"

HAS_BAXIAN_FIELD = {
    "controller_has_cards": {
        "zones": ["field"],
        "owner": "me",
        "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
        "min_count": 1,
    }
}

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "guided",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "selected_target",
                "zone": "field",
                "owner": "opponent",
                "card_filter": {"card_type_in": ["santo", "token"]},
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "decrease_strength", "amount": 5},
        },
        {
            "condition": HAS_BAXIAN_FIELD,
            "effect": {"action": "inflict_sin", "amount": 2, "target_player": "opponent"},
        },
    ],
}
