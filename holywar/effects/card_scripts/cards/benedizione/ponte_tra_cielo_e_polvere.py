from __future__ import annotations

CARD_NAME = "Ponte tra Cielo e Polvere"

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
            "target": {"type": "selected_target"},
            "effect": {"action": "store_target_name", "flag": "ponte_sacrificed_baxian_name"},
        },
        {
            "target": {"type": "selected_target"},
            "effect": {"action": "destroy_card"},
        },
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {
                    "name_contains": "ba xian",
                    "name_not_equals_stored": "ponte_sacrificed_baxian_name",
                    "card_type_in": ["santo", "token"],
                },
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "target": {"type": "selected_target"},
            "effect": {"action": "summon_target_to_field"},
        },
    ],
}
