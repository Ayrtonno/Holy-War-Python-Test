from __future__ import annotations

CARD_NAME = 'Giorno 1: Cieli e Terra'

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
                "zone": "deck",
                "owner": "me",
                "card_filter": {
                    "card_type_in": ["artefatto"],
                    "half_cost_lte_my_inspiration": True,
                },
                "min_targets": 1,
                "max_targets": 1,
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "summon_target_to_field_pay_half_inspiration", "target_player": "me", "placement_policy": "prompt_slot_required"},
                "placement_policy": "prompt_slot_required",
            "placement_policy": "prompt_slot_required",
        },
    ],
}
