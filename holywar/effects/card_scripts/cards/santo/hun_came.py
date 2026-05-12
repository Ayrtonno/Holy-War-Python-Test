from __future__ import annotations

CARD_NAME = """Hun-Came"""

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "noop",
    "on_enter_mode": "scripted",
    "on_activate_mode": "auto",
    "counted_bonuses": [],
    "faith_bonus_rules": [],
    "on_enter_actions": [
        {
            "activation_mode": "mandatory_auto",
            "target": {"type": "source_card"},
            "effect": {
                "action": "increase_source_stats_from_zone_count_div",
                "target_player": "me",
                "zone": "graveyard",
                "threshold": 5,
                "divisor": 5,
                "amount": 2,
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
        }
    ],
    "triggered_effects": [],
    "on_play_actions": [],
}
