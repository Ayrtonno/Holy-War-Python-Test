from __future__ import annotations

CARD_NAME = "Tikal"

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "activate_once_per_turn": True,
    "activate_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [],
    "on_activate_actions": [
        {
            "activation_mode": "mandatory_auto",
            "effect": {
                "action": "store_top_card_of_zone",
                "owner": "me",
                "zone": "deck",
                "position": "top",
                "store_as": "tikal_top",
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "effect": {
                "action": "reveal_stored_card",
                "stored": "tikal_top",
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {
                "stored_card_matches": {
                    "stored": "tikal_top",
                    "card_filter": {
                        "card_type_in": ["Santo"],
                    },
                }
            },
            "effect": {
                "action": "move_stored_card_to_zone",
                "stored": "tikal_top",
                "to_zone": "hand",
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {
                "not": {
                    "stored_card_matches": {
                        "stored": "tikal_top",
                        "card_filter": {
                            "card_type_in": ["Santo"],
                        },
                    }
                }
            },
            "effect": {
                "action": "move_stored_card_to_zone",
                "stored": "tikal_top",
                "to_zone": "deck_bottom",
            },
        },
    ],
}
