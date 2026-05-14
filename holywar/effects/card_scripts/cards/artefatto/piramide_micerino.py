from __future__ import annotations

CARD_NAME = """Piramide: Micerino"""

HAS_AT_LEAST_2_PYRAMIDS = {
    "controller_has_cards": {
        "zones": ["field"],
        "owner": "me",
        "card_filter": {"script_is_pyramid": True},
        "min_count": 2,
    }
}

HAS_AT_LEAST_3_PYRAMIDS = {
    "controller_has_cards": {
        "zones": ["field"],
        "owner": "me",
        "card_filter": {"script_is_pyramid": True},
        "min_count": 3,
    }
}

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "is_pyramid": True,
    "counted_bonuses": [
        {
            "context": "strength",
            "group": "pyramid_set_strength",
            "stacking": "max",
            "threshold": 1,
            "amount_mode": "flat",
            "amount": 5,
            "requirement": {
                "owner": "me",
                "zone": "artifacts",
                "card_filter": {"script_is_pyramid": True},
            },
        },
        {
            "context": "summon_faith",
            "group": "pyramid_set_summon_faith",
            "stacking": "max",
            "threshold": 2,
            "amount_mode": "base_faith_multiplier",
            "amount": 1,
            "requirement": {
                "owner": "me",
                "zone": "artifacts",
                "card_filter": {"script_is_pyramid": True},
            },
        },
        {
            "context": "turn_draw",
            "group": "pyramid_set_turn_draw",
            "stacking": "max",
            "threshold": 3,
            "amount_mode": "flat",
            "amount": 2,
            "requirement": {
                "owner": "me",
                "zone": "artifacts",
                "card_filter": {"script_is_pyramid": True},
            },
        },
    ],
    "triggered_effects": [],
    "on_play_actions": [
        {
            "condition": {"all_of": [HAS_AT_LEAST_2_PYRAMIDS, {"not": HAS_AT_LEAST_3_PYRAMIDS}]},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"card_type_in": ["santo", "token"]},
            },
            "effect": {"action": "increase_faith_equal_to_base"},
        },
    ],
}
