from __future__ import annotations

CARD_NAME = "Figli di Odino"

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "guided",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "selected_target",
                "zone": "field",
                "owner": "me",
                "card_filter": {
                    "card_type_in": ["santo"],
                },
                "min_targets": 1,
                "max_targets": 1,
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {
                "action": "increase_strength",
                "amount": 3,
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {
                "controller_has_saint_with_name": "Odino",
            },
            "target": {
                "type": "selected_target",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {
                "action": "increase_strength",
                "amount": 3,
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {
                "all_of": [
                    {"controller_has_saint_with_name": "Odino"},
                    {"controller_has_saint_with_name": "Thor"},
                ]
            },
            "effect": {
                "action": "draw_cards",
                "amount": 1,
                "target_player": "me",
            },
        },
    ],
}
