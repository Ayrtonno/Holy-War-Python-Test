from __future__ import annotations

CARD_NAME = "Giardino del Loto Inverso"

HAS_3_DISTINCT = {
    "controller_has_distinct_cards_gte": {
        "zones": ["field"],
        "owner": "me",
        "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
        "min_count": 3,
    }
}

SOURCE_TARGET = {
    "type": "source_card",
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
    "play_targeting": "none",
    "triggered_effects": [
        {
            "trigger": {"event": "on_my_turn_start", "frequency": "each_turn", "condition": {"not": HAS_3_DISTINCT}},
            "target": SOURCE_TARGET,
            "effect": {"action": "giardino_loto_resolution", "amount": 4},
        },
        {
            "trigger": {"event": "on_my_turn_start", "frequency": "each_turn", "condition": HAS_3_DISTINCT},
            "target": SOURCE_TARGET,
            "effect": {"action": "remove_sin", "amount": 4, "target_player": "me"},
        },
        {
            "trigger": {"event": "on_my_turn_start", "frequency": "each_turn", "condition": HAS_3_DISTINCT},
            "target": SOURCE_TARGET,
            "effect": {"action": "inflict_sin", "amount": 4, "target_player": "opponent"},
        },
    ],
    "on_play_actions": [],
}
