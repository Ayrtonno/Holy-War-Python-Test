from __future__ import annotations

CARD_NAME = "Patto dei Reishi"

HAS_3_BAXIAN = {
    "controller_has_cards": {
        "zones": ["field"],
        "owner": "me",
        "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
        "min_count": 3,
    }
}

SELECTED_TARGET = {
    "type": "selected_target",
    "target_policy": "optional_resolve",
    "selection_mode": "prompt",
    "cancel_behavior": "abort_step",
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
    "play_targeting": "auto",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {"activation_mode": "mandatory_auto", "condition": {"not": HAS_3_BAXIAN}, "target": SELECTED_TARGET, "effect": {"action": "increase_strength", "amount": 2}},
        {"activation_mode": "mandatory_auto", "condition": {"not": HAS_3_BAXIAN}, "target": SELECTED_TARGET, "effect": {"action": "increase_faith", "amount": 2}},
        {"activation_mode": "mandatory_auto", "condition": HAS_3_BAXIAN, "target": SELECTED_TARGET, "effect": {"action": "increase_strength", "amount": 4}},
        {"activation_mode": "mandatory_auto", "condition": HAS_3_BAXIAN, "target": SELECTED_TARGET, "effect": {"action": "increase_faith", "amount": 4}},
    ],
}

