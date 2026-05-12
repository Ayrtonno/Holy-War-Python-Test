from __future__ import annotations

CARD_NAME = "Zhang Guolao"

HAS_3_BAXIAN_FIELD = {
    "controller_has_cards": {
        "zones": ["field"],
        "owner": "me",
        "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
        "min_count": 3,
    }
}

HAS_BAXIAN_GRAVE = {
    "controller_has_cards": {
        "zones": ["graveyard"],
        "owner": "me",
        "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
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
            "condition": {"all_of": [HAS_3_BAXIAN_FIELD, HAS_BAXIAN_GRAVE]},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "condition": {"all_of": [HAS_3_BAXIAN_FIELD, HAS_BAXIAN_GRAVE, {"selected_target_exists": True}]},
            "target": {"type": "selected_target"},
            "effect": {"action": "summon_target_to_field"},
        },
        {
            "condition": {"all_of": [{"not": HAS_3_BAXIAN_FIELD}, HAS_BAXIAN_GRAVE]},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "condition": {"all_of": [{"not": HAS_3_BAXIAN_FIELD}, HAS_BAXIAN_GRAVE, {"selected_target_exists": True}]},
            "target": {"type": "selected_target"},
            "effect": {"action": "move_to_hand"},
        },
    ],
}
