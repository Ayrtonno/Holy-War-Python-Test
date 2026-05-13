from __future__ import annotations

CARD_NAME = "Convocazione degli Otto"

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
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "selected_target",
                "zone": "relicario",
                "owner": "me",
                "card_filter": {"name_in": BAXIAN_NAMES, "card_type_in": ["santo", "token"]},
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "move_to_hand"},
        },
        {"effect": {"action": "shuffle_deck", "target_player": "me"}},
        {
            "condition": HAS_BAXIAN_FIELD,
            "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"},
        },
    ],
}
