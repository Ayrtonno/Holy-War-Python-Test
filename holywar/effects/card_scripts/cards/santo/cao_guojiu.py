from __future__ import annotations

CARD_NAME = "Cao Guojiu"

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

DISTINCT_4 = {
    "controller_has_distinct_cards_gte": {
        "zones": ["field"],
        "owner": "me",
        "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
        "min_count": 4,
    }
}
DISTINCT_6 = {
    "controller_has_distinct_cards_gte": {
        "zones": ["field"],
        "owner": "me",
        "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
        "min_count": 6,
    }
}

SCRIPT = {
    "on_play_mode": "auto",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "protection_rules": [
        {
            "event": "target_by_effect",
            "source_owner": "enemy",
            "target_owner": "friendly",
            "target_names": BAXIAN_NAMES,
        }
    ],
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_card_played",
                "frequency": "each_time",
                "condition": {
                    "all_of": [
                        {"event_card_owner": "opponent"},
                        {"event_card_type_in": ["benedizione", "maledizione"]},
                        DISTINCT_4,
                    ]
                },
            },
            "target": {"type": "source_card"},
            "effect": {"action": "negate_next_activation", "target_player": "opponent"},
        },
        {
            "trigger": {
                "event": "on_card_played",
                "frequency": "each_time",
                "condition": {
                    "all_of": [
                        {"event_card_owner": "opponent"},
                        DISTINCT_6,
                    ]
                },
            },
            "target": {"type": "source_card"},
            "effect": {"action": "negate_next_activation", "target_player": "opponent"},
        },
    ],
    "on_play_actions": [],
}
