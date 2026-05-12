from __future__ import annotations

CARD_NAME = """Larva Pestilenziale"""

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
                "event": "on_this_card_destroyed",
                "frequency": "each_turn",
                "condition": {"payload_reason_in": ["battle"]},
            },
            "target": {"type": "event_source_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "halve_strength_rounded_down"},
        }
    ],
    "on_play_actions": [],
}
