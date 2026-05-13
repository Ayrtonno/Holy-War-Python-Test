from __future__ import annotations

CARD_NAME = "Eco dei Nomi Immortali"

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "auto",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "hand",
                "owner": "me",
                "card_filter": {
                    "name_in": [
                        "han xiangzi",
                        "li tieguai",
                        "zhang guolao",
                        "lu dongbin",
                        "lan caihe",
                        "he xiangu",
                        "zhongli quan",
                        "cao guojiu",
                    ],
                    "card_type_in": ["santo", "token"],
                },
                "max_targets": 3,
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "store_target_count", "flag": "eco_baxian_hand_count"},
        },
        {
            "activation_mode": "mandatory_auto",
            "effect": {"action": "draw_cards_from_flag", "flag": "eco_baxian_hand_count", "target_player": "me"},
        },
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "hand",
                "owner": "me",
                "card_filter": {"exclude_event_card": True},
                "min_targets": 1,
                "max_targets": 1,
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "selected_target",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "move_to_relicario"},
        },
        { "activation_mode": "mandatory_auto","effect": {"action": "shuffle_deck", "target_player": "me"}},
    ],
}
