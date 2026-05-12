from __future__ import annotations

CARD_NAME = 'Collasso'

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "activation_mode": "mandatory_auto",
            "condition": {
                "all_of": [
                    {
                        "controller_has_cards": {
                            "owner": "me",
                            "zone": "building",
                            "min_count": 1,
                        }
                    },
                    {
                        "controller_has_cards": {
                            "owner": "opponent",
                            "zone": "building",
                            "min_count": 1,
                        }
                    },
                ]
            },
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"card_type_in": ["artefatto"]},
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
                        "controller_has_cards": {
                            "owner": "me",
                            "zone": "building",
                            "min_count": 1,
                        }
                    },
                    {
                        "controller_has_cards": {
                            "owner": "opponent",
                            "zone": "building",
                            "min_count": 1,
                        }
                    },
                ]
            },
            "target": { "target_policy": "optional_resolve", "selection_mode": "prompt", "cancel_behavior": "abort_step","type": "selected_targets"},
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "destroy_card"},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {
                "all_of": [
                    {
                        "controller_has_cards": {
                            "owner": "me",
                            "zone": "building",
                            "min_count": 1,
                        }
                    },
                    {
                        "controller_has_cards": {
                            "owner": "opponent",
                            "zone": "building",
                            "min_count": 1,
                        }
                    },
                ]
            },
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "opponent",
                "card_filter": {"card_type_in": ["artefatto"]},
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
                        "controller_has_cards": {
                            "owner": "me",
                            "zone": "building",
                            "min_count": 1,
                        }
                    },
                    {
                        "controller_has_cards": {
                            "owner": "opponent",
                            "zone": "building",
                            "min_count": 1,
                        }
                    },
                ]
            },
            "target": { "target_policy": "optional_resolve", "selection_mode": "prompt", "cancel_behavior": "abort_step","type": "selected_targets"},
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "destroy_card"},
        },
    ],
}
