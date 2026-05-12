from __future__ import annotations

CARD_NAME = "Spada Purificante di Lu Dongbin"

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [],
    "counted_bonuses": [
        {
            "context": "incoming_damage_reduction_from_enemy_saints",
            "amount_mode": "per_count_div_floor",
            "divisor": 1,
            "amount": 2,
            "stacking": "sum",
            "requirement": {
                "zones": ["field"],
                "owner": "me",
                "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
            },
            "distinct_by_name": True,
        }
    ],
}
