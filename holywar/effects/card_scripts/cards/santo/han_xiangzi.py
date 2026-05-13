from __future__ import annotations

CARD_NAME = "Han Xiangzi"

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

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "auto",
    "on_enter_mode": "scripted",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [],
    "on_enter_actions": [
        {
            "activation_mode": "mandatory_auto",
            "effect": {
                "action": "draw_cards_and_store_last_drawn",
                "amount": 1,
                "target_player": "me",
                "store_as": "han_draw_1",
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "source_card",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "reveal_stored_card", "stored": "han_draw_1"},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {
                "stored_card_matches": {
                    "stored": "han_draw_1",
                    "card_filter": {"name_in": BA_XIAN_NAMES, "card_type_in": ["santo", "token"]},
                }
            },
            "effect": {
                "action": "draw_cards_and_store_last_drawn",
                "amount": 1,
                "target_player": "me",
                "store_as": "han_draw_2",
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {
                "stored_card_matches": {
                    "stored": "han_draw_1",
                    "card_filter": {"name_in": BA_XIAN_NAMES, "card_type_in": ["santo", "token"]},
                }
            },
            "target": {
                "type": "source_card",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "reveal_stored_card", "stored": "han_draw_2"},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {
                "stored_card_matches": {
                    "stored": "han_draw_1",
                    "card_filter": {"name_in": BA_XIAN_NAMES, "card_type_in": ["santo", "token"]},
                }
            },
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "hand",
                "owner": "me",
                "max_targets": 1,
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {
                "all_of": [
                    {
                        "stored_card_matches": {
                            "stored": "han_draw_1",
                            "card_filter": {"name_in": BA_XIAN_NAMES, "card_type_in": ["santo", "token"]},
                        }
                    },
                    {"selected_target_exists": True},
                ]
            },
            "target": {
                "type": "selected_target",
                "zone": "hand",
                "owner": "me",
                "min_targets": 1,
                "max_targets": 1,
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "send_to_graveyard"},
        },
    ],
}
