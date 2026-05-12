from __future__ import annotations

CARD_NAME = "Aquila Vorace"

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_this_card_kills_in_battle",
                "frequency": "each_turn",
            },
            "target": {"type": "event_card"},
            "effect": {
                "action": "return_to_hand_once_per_turn",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            }
        }
    ],
    "on_play_actions": [],
}
