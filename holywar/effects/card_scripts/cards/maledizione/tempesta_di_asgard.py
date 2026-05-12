from __future__ import annotations

CARD_NAME = """Tempesta di Asgard"""

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
            "condition": {"controller_has_saint_with_name": "Thor"},
            "target": {
                "type": "all_saints_on_field",
                "card_filter": {"card_type_in": ["santo", "token"]},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "decrease_faith", "amount": 4},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {"not": {"controller_has_saint_with_name": "Thor"}},
            "target": {
                "type": "all_saints_on_field",
                "card_filter": {"card_type_in": ["santo", "token"]},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "decrease_faith", "amount": 2},
        },
    ],
}
