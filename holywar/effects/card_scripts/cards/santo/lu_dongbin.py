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

HAS_OPP_ARTIFACT = {
    "controller_has_cards": {
        "zones": ["field"],
        "owner": "opponent",
        "card_filter": {"card_type_in": ["artefatto"]},
        "min_count": 1,
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
            "condition": {"all_of": [HAS_OTHER_BAXIAN, HAS_OPP_ARTIFACT]},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "opponent",
                "card_filter": {"card_type_in": ["artefatto"]},
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "condition": {
                "all_of": [
                    HAS_OTHER_BAXIAN,
                    HAS_OPP_ARTIFACT,
                    {"selected_target_exists": True},
                ]
            },
            "target": {"type": "selected_target"},
            "effect": {"action": "destroy_card"},
        },
        {
            "condition": {"not": HAS_OTHER_BAXIAN},
            "target": {"type": "source_card"},
            "effect": {"action": "increase_strength", "amount": 2},
        },
    ],
}
