from __future__ import annotations

CARD_NAME = "Giudizio delle Otto Tracce"

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
            "effect": {
                "action": "store_distinct_count",
                "flag": "gd8_max_targets",
                "requirement": {
                    "zones": ["hand", "field", "graveyard"],
                    "owner": "me",
                    "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
                },
            }
        },
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "opponent",
                "card_filter": {"card_type_in": ["santo", "token", "artefatto", "edificio"]},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "choose_targets", "min_targets": 0, "max_targets": 8, "flag": "gd8_max_targets"},
        },
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "selected_targets",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "store_target_count", "flag": "gd8_destroyed_count"},
        },
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "selected_targets",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "destroy_card"},
        },
        { "activation_mode": "mandatory_auto","effect": {"action": "inflict_sin_from_flag_scaled", "flag": "gd8_destroyed_count", "amount": 5, "target_player": "opponent"}},
        { "activation_mode": "mandatory_auto","effect": {"action": "remove_sin_from_flag_scaled", "flag": "gd8_destroyed_count", "amount": 3, "target_player": "me"}},
    ],
}
