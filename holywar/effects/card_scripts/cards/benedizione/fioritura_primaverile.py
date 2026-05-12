from __future__ import annotations

CARD_NAME = 'Fioritura Primaverile'

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
                "type": "cards_controlled_by_owner",
                "owner": "me",
                "zone": "field",
                "card_filter": {
                    "card_type_in": ["santo", "token"],
                    "expansion_in": ["ANI-1"],
                },
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "increase_faith", "amount": 2},
        },
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "cards_controlled_by_owner",
                "owner": "me",
                "zone": "field",
                "card_filter": {
                    "card_type_in": ["santo", "token"],
                    "expansion_in": ["ANI-1"],
                },
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "increase_strength", "amount": 2},
        },
    ],
}
