from __future__ import annotations

CARD_NAME = "Eco dei Nomi Immortali"

BAXIAN_NAMES = [
    "Lu Dongbin",
    "He Xian'gu",
    "Li Tieguai",
    "Han Xiangzi",
    "Lan Caihe",
    "Zhang Guolao",
    "Cao Guojiu",
    "Zhongli Quan",
]

HAS_BAXIAN_FIELD = {
    "controller_has_cards": {
        "zones": ["field"],
        "owner": "me",
        "card_filter": {"name_in": BAXIAN_NAMES, "card_type_in": ["santo", "token"]},
        "min_count": 1,
    }
}

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "auto",
    "play_requirements": HAS_BAXIAN_FIELD,
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "selected_target",
                "zone": "field",
                "owner": "me",
                "card_filter": {"name_in": BAXIAN_NAMES, "card_type_in": ["santo", "token"]},
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "target": {"type": "selected_target"},
            "effect": {"action": "store_target_name", "flag": "eco_nomi_field_baxian_name"},
        },
        {
            "target": {
                "type": "selected_target",
                "zone": "hand",
                "owner": "me",
                "card_filter": {
                    "name_in": BAXIAN_NAMES,
                    "name_not_equals_stored": "eco_nomi_field_baxian_name",
                    "card_type_in": ["santo", "token"],
                },
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "summon_target_to_field"},
        },
    ],
}
