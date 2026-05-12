from __future__ import annotations

CARD_NAME = 'Avidità di Av'

SCRIPT = {
    "default_target_policy": "optional_resolve",
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "activation_mode": "mandatory_auto",
            "effect": {"action": "draw_cards", "amount": 3, "target_player": "me"},
        },
        {
            "activation_mode": "mandatory_auto",
            "effect": {"action": "draw_cards", "amount": 3, "target_player": "opponent"},
        },
    ],
}
