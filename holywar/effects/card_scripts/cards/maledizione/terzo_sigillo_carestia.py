from __future__ import annotations

CARD_NAME = 'Terzo Sigillo: Carestia'

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
            "target": { "target_policy": "optional_resolve", "selection_mode": "prompt", "cancel_behavior": "abort_step","type": "source_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "set_next_turn_draw_override", "amount": 1, "target_player": "opponent"},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {"controller_altare_sigilli_gte": 4},
            "target": {
                "type": "all_saints_on_field",
                "owner": "opponent",
                "card_filter": {"card_type_in": ["santo", "token"]},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "decrease_faith", "amount": 2},
        },
    ],
}
