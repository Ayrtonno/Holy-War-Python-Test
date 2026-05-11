from __future__ import annotations

CARD_NAME = "Lu Dongbin"

HAS_OTHER_BAXIAN = {
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
            "condition": HAS_OTHER_BAXIAN,
            "target": {
                "type": "selected_target",
                "zone": "field",
                "owner": "opponent",
                "card_filter": {"card_type_in": ["artefatto"]},
                "min_targets": 0,
                "max_targets": 1,
            },
            "effect": {"action": "destroy_card"},
        },
        {
            "condition": {"not": HAS_OTHER_BAXIAN},
            "target": {"type": "source_card"},
            "effect": {"action": "increase_strength", "amount": 2},
        },
    ],
}
