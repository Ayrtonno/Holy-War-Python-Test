from __future__ import annotations

CARD_NAME = """Xibalba"""

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
                "event": "on_summoned_from_graveyard",
                "frequency": "each_time",
                "condition": {"event_card_type_in": ["santo"]},
            },
            "target": {"type": "event_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "increase_faith", "amount": 5},
        },
        {
            "trigger": {
                "event": "on_summoned_from_graveyard",
                "frequency": "each_time",
                "condition": {"event_card_type_in": ["santo"]},
            },
            "target": {"type": "event_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "increase_strength", "amount": 5},
        },
        {
            "trigger": {
                "event": "on_summoned_from_graveyard",
                "frequency": "each_time",
                "condition": {"event_card_type_in": ["santo"]},
            },
            "target": {"type": "none"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "remove_sin", "amount": 3, "target_player": "me"},
        },
    ],
    "on_play_actions": [],
}