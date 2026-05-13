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

HAS_1 = {
    "controller_has_cards": {
        "zones": ["hand"],
        "owner": "me",
        "card_filter": {"name_in": BAXIAN_NAMES, "card_type_in": ["santo", "token"]},
        "min_count": 1,
    }
}
HAS_2 = {
    "controller_has_cards": {
        "zones": ["hand"],
        "owner": "me",
        "card_filter": {"name_in": BAXIAN_NAMES, "card_type_in": ["santo", "token"]},
        "min_count": 2,
    }
}
HAS_3 = {
    "controller_has_cards": {
        "zones": ["hand"],
        "owner": "me",
        "card_filter": {"name_in": BAXIAN_NAMES, "card_type_in": ["santo", "token"]},
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
        {"condition": HAS_1, "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"}},
        {"condition": HAS_2, "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"}},
        {"condition": HAS_3, "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"}},
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "hand",
                "owner": "me",
                "card_filter": {"exclude_event_card": True},
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "target": {"type": "selected_target"},
            "effect": {"action": "move_to_relicario"},
        },
        {"effect": {"action": "shuffle_deck", "target_player": "me"}},
    ],
}
