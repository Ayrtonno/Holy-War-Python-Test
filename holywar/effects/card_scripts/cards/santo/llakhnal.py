from __future__ import annotations

CARD_NAME = """Llakhnal"""

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "attack_targeting": "untargetable",
    "triggered_effects": [
        {
            "trigger": {"event": "on_turn_start", "frequency": "each_time"},
            "target": {"type": "source_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "destroy_card"},
        },
    ],
    "on_play_actions": [],
}

