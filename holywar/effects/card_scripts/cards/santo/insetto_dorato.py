from __future__ import annotations

CARD_NAME = """Insetto Dorato"""

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "can_attack_multiple_targets_in_attack_per_turn": True,
    "triggered_effects": [
        {
            "trigger": {"event": "on_this_card_deals_damage", "frequency": "each_time"},
            "target": {"type": "source_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "increase_strength", "amount": 1},
        }
    ],
    "on_play_actions": [],
}
