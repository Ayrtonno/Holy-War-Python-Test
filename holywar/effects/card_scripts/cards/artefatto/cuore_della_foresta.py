from __future__ import annotations

CARD_NAME = "Cuore della foresta"

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_saint_defeated_in_battle",
                "frequency": "each_turn",
            },
            "condition": {
                "event_card_name_is": "Token Albero",
            },
            "target": {
                "type": "none",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {
                "action": "inflict_sin",
                "amount": 1,
                "target_player": "opponent",
            },
        }
    ],
    "on_play_actions": [],
}