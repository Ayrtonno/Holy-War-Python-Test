from __future__ import annotations

CARD_NAME = 'Rituale dei Guardiani'

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "guided",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "selected_target",
                "zone": "field",
                "owner": "me",
                "min_targets": 1,
                "max_targets": 1,
                "card_filter": {"card_type_in": ["santo"]},
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "move_to_graveyard"},
        },
        {
            "activation_mode": "mandatory_auto",
            "target": { "target_policy": "optional_resolve", "selection_mode": "prompt", "cancel_behavior": "abort_step","type": "source_card"},
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"},
        },
        {
            "activation_mode": "mandatory_auto",
            "target": { "target_policy": "optional_resolve", "selection_mode": "prompt", "cancel_behavior": "abort_step","type": "source_card"},
            "effect": {
                "action": "store_top_card_of_zone",
                "owner": "me",
                "zone": "hand",
                "position": "top",
                "store_as": "rituale_guardiani_drawn",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "target": { "target_policy": "optional_resolve", "selection_mode": "prompt", "cancel_behavior": "abort_step","type": "source_card"},
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "reveal_stored_card", "stored": "rituale_guardiani_drawn"},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {
                "stored_card_matches": {
                    "stored": "rituale_guardiani_drawn",
                    "card_filter": {"card_type_in": ["santo"]},
                }
            },
            "target": { "target_policy": "optional_resolve", "selection_mode": "prompt", "cancel_behavior": "abort_step","type": "source_card"},
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "summon_stored_card_to_field", "stored": "rituale_guardiani_drawn", "placement_policy": "prompt_slot_required"},
            "placement_policy": "prompt_slot_required",
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {
                "not": {
                    "stored_card_matches": {
                        "stored": "rituale_guardiani_drawn",
                        "card_filter": {"card_type_in": ["santo"]},
                    }
                }
            },
            "target": { "target_policy": "optional_resolve", "selection_mode": "prompt", "cancel_behavior": "abort_step","type": "source_card"},
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "move_stored_card_to_zone", "stored": "rituale_guardiani_drawn", "to_zone": "graveyard"},
        },
    ],
}
