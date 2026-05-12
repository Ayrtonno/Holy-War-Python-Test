from __future__ import annotations

CARD_NAME = 'Secondo Sigillo: Guerra'

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
            "condition": {"controller_altare_sigilli_gte": 3},
            "target": {
                "type": "selected_targets",
                "zone": "field",
                "owner": "any",
                "card_filter": {"card_type_in": ["santo", "token"]},
                "min_targets": 2,
                "max_targets": 2,
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "destroy_card"},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {"not": {"controller_altare_sigilli_gte": 3}},
            "target": {
                "type": "selected_target",
                "zone": "field",
                "owner": "any",
                "card_filter": {
                    "card_type_in": ["santo", "token"],
                    "strength_gte": 4,
                },
                "min_targets": 1,
                "max_targets": 1,
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "destroy_card"},
        },
    ],
}
