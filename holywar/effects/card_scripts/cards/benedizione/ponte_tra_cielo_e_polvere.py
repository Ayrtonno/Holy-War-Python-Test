from __future__ import annotations

CARD_NAME = "Ponte tra Cielo e Polvere"

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
                "card_filter": {"name_in": BAXIAN_NAMES, "card_type_in": ["santo", "token"]},
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "target": {"type": "selected_target"},
            "effect": {"action": "store_target_uid", "flag": "ponte_sacrificed_baxian_uid"},
        },
        {
            "target": {"type": "selected_target"},
            "effect": {"action": "store_target_name", "flag": "ponte_sacrificed_baxian_name"},
        },
        {
            "effect": {"action": "destroy_stored_card", "stored": "ponte_sacrificed_baxian_uid"},
        },
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {
                    "name_in": BAXIAN_NAMES,
                    "name_not_equals_stored": "ponte_sacrificed_baxian_name",
                    "card_type_in": ["santo", "token"],
                },
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "target": {
                "type": "selected_target",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {
                    "name_in": BAXIAN_NAMES,
                    "name_not_equals_stored": "ponte_sacrificed_baxian_name",
                    "card_type_in": ["santo", "token"],
                },
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "store_target_uid", "flag": "ponte_grave_pick_uid"},
        },
        {
            "effect": {"action": "summon_stored_card_to_field", "stored": "ponte_grave_pick_uid"},
        },
    ],
}
