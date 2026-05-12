from __future__ import annotations

CARD_NAME = """Sabbie Mobili"""

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
            "trigger": {"event": "on_attack_declared", "frequency": "each_time"},
            "condition": {"event_card_owner_attack_count_gte": 1},
            "target": {"type": "event_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "prevent_specific_card_from_attacking", "amount": 1},
        }
    ],
    "on_play_actions": [],
}
