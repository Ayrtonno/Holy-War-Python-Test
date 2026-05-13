from __future__ import annotations

CARD_NAME = "Spirito dell'Esercito Dorato"

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "triggered_effects": [
        {
            "trigger": {"event": "on_my_turn_start", "frequency": "each_turn"},
            "target": {
                "type": "none",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "pay_sin_or_destroy_self", "amount": 5},
        }
    ],
    "on_activate_actions": [
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "none",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {
                "action": "summon_token",
                "card_name": "Spirito Vacuo",
            },
        }
    ],
    "on_play_actions": [],
}
