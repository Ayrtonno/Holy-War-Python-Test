from __future__ import annotations

CARD_NAME = "Ponte tra Cielo e Polvere"

SELECTED_TARGET = {
    "type": "selected_target",
    "target_policy": "optional_resolve",
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
    "on_activate_mode": "auto",
    "play_targeting": "auto",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {"activation_mode": "mandatory_auto", "target": SELECTED_TARGET, "effect": {"action": "store_target_name", "flag": "ponte_sacrificed_baxian_name"}},
        {"activation_mode": "mandatory_auto", "target": SELECTED_TARGET, "effect": {"action": "destroy_card"}},
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {
                    "name_contains": "ba xian",
                    "name_not_equals_stored": "ponte_sacrificed_baxian_name",
                    "card_type_in": ["santo", "token"],
                },
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {"activation_mode": "mandatory_auto", "target": SELECTED_TARGET, "effect": {"action": "summon_target_to_field", "placement_policy": "prompt_slot_required"}},
    ],
}
