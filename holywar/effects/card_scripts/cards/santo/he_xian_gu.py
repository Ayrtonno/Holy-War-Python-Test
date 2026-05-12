from __future__ import annotations

CARD_NAME = "He Xian'gu"

HAS_2_BAXIAN_GRAVE = {
    "controller_has_cards": {
        "zones": ["graveyard"],
        "owner": "me",
        "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
        "min_count": 2,
    }
}

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
    "on_play_actions": [
        {
            "activation_mode": "mandatory_auto",
            "condition": HAS_2_BAXIAN_GRAVE,
            "effect": {"action": "remove_sin", "amount": 8, "target_player": "me"},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {"not": HAS_2_BAXIAN_GRAVE},
            "effect": {"action": "remove_sin", "amount": 4, "target_player": "me"},
        },
    ],
}
