from __future__ import annotations

CARD_NAME = "Legame Primordiale"

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
                "type": "selected_targets",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {
                    "crosses_lte": 7,
                },
                "min_targets": 1,
                "max_targets_from": {
                    "count_cards_controlled_by_owner": {
                        "owner": "me",
                        "zone": "field",
                        "card_filter": {
                            "name_contains": "albero",
                            "card_type_in": ["santo", "token"],
                        },
                    }
                },
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {
                "action": "move_to_relicario",
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "effect": {
                "action": "shuffle_deck",
                "target_player": "me",
            },
        },
    ],
}