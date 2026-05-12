from __future__ import annotations

CARD_NAME = """Albero Secolare"""

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
            "trigger": {"event": "on_this_card_receives_damage", "frequency": "each_turn"},
            "condition": {"target_current_faith_gte": 1},
            "target": {"type": "event_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "increase_faith", "amount": 7},
        }
    ],
    "on_play_actions": [],
}

