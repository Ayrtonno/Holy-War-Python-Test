from __future__ import annotations

CARD_NAME = """Mjolnir"""

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "noop",
    "play_requirements": {
        "controller_has_cards": {
            "owner": "me",
            "zones": ["artifacts"],
            "card_filter": {"name_equals": "Járngreipr"},
            "min_count": 1,
        },
        "can_play_by_sacrificing": {
            "owner": "me",
            "zones": ["artifacts"],
            "card_filter": {"name_equals": "Járngreipr"},
            "count": 1,
        },
    },
    "play_targeting": "none",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "on_play_actions": [],
}

