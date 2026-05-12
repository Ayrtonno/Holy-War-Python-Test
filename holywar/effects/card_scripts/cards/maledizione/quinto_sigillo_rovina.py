from __future__ import annotations

CARD_NAME = "Quinto Sigillo: Rovina"

TARGET_FILTER = {"card_type_in": ["artefatto", "edificio"]}

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
            "condition": {"controller_altare_sigilli_gte": 6},
            "target": {
                "type": "selected_targets",
                "zone": "field",
                "owner": "opponent",
                "card_filter": TARGET_FILTER,
                "min_targets": 1,
                "max_targets": 2,
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "destroy_card"},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {"not": {"controller_altare_sigilli_gte": 6}},
            "target": {
                "type": "selected_target",
                "zone": "field",
                "owner": "opponent",
                "card_filter": TARGET_FILTER,
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

