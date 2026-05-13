from __future__ import annotations

CARD_NAME = "Giardino del Loto Inverso"

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

HAS_3_DISTINCT = {
    "controller_has_distinct_cards_gte": {
        "zones": ["field"],
        "owner": "me",
        "card_filter": {"name_in": BAXIAN_NAMES, "card_type_in": ["santo", "token"]},
        "min_count": 3,
    }
}

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_my_turn_start",
                "frequency": "each_turn",
                "condition": {"not": HAS_3_DISTINCT},
            },
            "target": {"type": "source_card"},
            "effect": {
                "action": "choose_option",
                "choice_title": "Giardino del Loto Inverso",
                "choice_prompt": "Scegli un effetto:",
                "choice_options": [
                    {"label": "Rimuovi 4 Peccato", "value": "heal"},
                    {"label": "Infliggi 4 Peccato", "value": "hit"},
                ],
            },
        },
        {
            "trigger": {
                "event": "on_my_turn_start",
                "frequency": "each_turn",
                "condition": {"all_of": [{"not": HAS_3_DISTINCT}, {"selected_option_in": ["heal"]}]},
            },
            "target": {"type": "source_card"},
            "effect": {"action": "remove_sin", "amount": 4, "target_player": "me"},
        },
        {
            "trigger": {
                "event": "on_my_turn_start",
                "frequency": "each_turn",
                "condition": {"all_of": [{"not": HAS_3_DISTINCT}, {"selected_option_in": ["hit"]}]},
            },
            "target": {"type": "source_card"},
            "effect": {"action": "inflict_sin", "amount": 4, "target_player": "opponent"},
        },
        {
            "trigger": {"event": "on_my_turn_start", "frequency": "each_turn", "condition": HAS_3_DISTINCT},
            "target": {"type": "source_card"},
            "effect": {"action": "remove_sin", "amount": 4, "target_player": "me"},
        },
        {
            "trigger": {"event": "on_my_turn_start", "frequency": "each_turn", "condition": HAS_3_DISTINCT},
            "target": {"type": "source_card"},
            "effect": {"action": "inflict_sin", "amount": 4, "target_player": "opponent"},
        },
    ],
    "on_play_actions": [],
}
