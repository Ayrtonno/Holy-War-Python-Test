from __future__ import annotations

CARD_NAME = "Borraccia di Li Tieguai"

BA_XIAN_NAMES = [
    "Lu Dongbin",
    "He Xian'gu",
    "Li Tieguai",
    "Han Xiangzi",
    "Lan Caihe",
    "Zhang Guolao",
    "Cao Guojiu",
    "Zhongli Quan",
]

BAXIAN_DESTROYED = {
    "all_of": [
        {"event_card_owner": "me"},
        {"event_card_type_in": ["santo", "token"]},
        {"any_of": [{"event_card_name_is": n} for n in BA_XIAN_NAMES]},
        {"payload_from_zone_in": ["attack", "defense", "field"]},
    ]
}

SOURCE_TARGET = {
    "type": "source_card",
    "target_policy": "optional_resolve",
    "selection_mode": "prompt",
    "cancel_behavior": "abort_step",
}

GRAVE_BAXIAN_TARGET = {
    "type": "selected_target",
    "zone": "graveyard",
    "owner": "me",
    "card_filter": {"name_in": BA_XIAN_NAMES, "card_type_in": ["santo", "token"]},
    "min_targets": 1,
    "max_targets": 1,
    "target_policy": "required_to_resolve",
    "selection_mode": "prompt",
    "cancel_behavior": "abort_step",
}

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "activate_once_per_turn": True,
    "play_targeting": "none",
    "activate_targeting": "none",
    "triggered_effects": [
        {
            "trigger": {"event": "on_card_sent_to_graveyard", "frequency": "each_time", "condition": BAXIAN_DESTROYED},
            "target": SOURCE_TARGET,
            "effect": {"action": "campana_add_counter"},
        }
    ],
    "on_play_actions": [],
    "on_activate_actions": [
        {
            "activation_mode": "mandatory_auto",
            "effect": {
                "action": "choose_option",
                "choice_title": "Borraccia",
                "choice_prompt": "Scegli l'effetto.",
                "choice_options": [
                    {
                        "label": "Rimuovi 2: aggiungi alla mano",
                        "value": "hand",
                        "condition": {
                            "all_of": [
                                {"source_counter_gte": 2},
                                {
                                    "controller_has_cards": {
                                        "zone": "graveyard",
                                        "owner": "me",
                                        "card_filter": {"name_in": BA_XIAN_NAMES, "card_type_in": ["santo", "token"]},
                                        "min_count": 1,
                                    }
                                },
                            ]
                        },
                    },
                    {
                        "label": "Rimuovi 5: evoca",
                        "value": "summon",
                        "condition": {
                            "all_of": [
                                {"source_counter_gte": 5},
                                {
                                    "controller_has_cards": {
                                        "zone": "graveyard",
                                        "owner": "me",
                                        "card_filter": {"name_in": BA_XIAN_NAMES, "card_type_in": ["santo", "token"]},
                                        "min_count": 1,
                                    }
                                },
                            ]
                        },
                    },
                ],
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {"all_of": [{"selected_option_in": ["hand"]}, {"source_counter_gte": 2}]},
            "target": SOURCE_TARGET,
            "effect": {"action": "campana_remove_counter", "amount": 2},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {"all_of": [{"selected_option_in": ["hand"]}, {"source_counter_gte": 2}]},
            "target": GRAVE_BAXIAN_TARGET,
            "effect": {"action": "move_to_hand"},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {"all_of": [{"selected_option_in": ["summon"]}, {"source_counter_gte": 5}]},
            "target": SOURCE_TARGET,
            "effect": {"action": "campana_remove_counter", "amount": 5},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {"all_of": [{"selected_option_in": ["summon"]}, {"source_counter_gte": 5}]},
            "target": GRAVE_BAXIAN_TARGET,
            "effect": {"action": "summon_target_to_field", "placement_policy": "prompt_slot_required"},
        },
    ],
}
