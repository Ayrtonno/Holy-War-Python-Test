from __future__ import annotations

CARD_NAME = """Prete Anziano"""

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "auto",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_this_card_attacks", "frequency": "each_turn"},
            "target": {"type": "source_card"},
            "effect": {
                "action": "remove_sin",
                "amount": 3,
                "target_player": "me",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            }
        }
    ],
    "on_play_actions": [],
}
