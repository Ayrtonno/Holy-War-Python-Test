from __future__ import annotations

CARD_NAME = "Risveglio di Ph-Dak'Gaph"

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "selected_targets",
                "zone": "excommunicated",
                "owner": "me",
                "min_targets": 1,
                "max_targets": 5,
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {
                "action": "move_to_hand",
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "effect": {
                "action": "remove_sin",
                "amount": 10,
                "target_player": "me",
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "effect": {
                "action": "move_source_to_zone",
                "to_zone": "excommunicated",
            },
        },
    ],
}
