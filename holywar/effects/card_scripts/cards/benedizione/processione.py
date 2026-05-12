from __future__ import annotations

CARD_NAME = "Processione"

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
    "play_requirements": {
        "controller_hand_size_lte": 7
    },
    "triggered_effects": [],
    "on_play_actions": [
        {
            "activation_mode": "mandatory_auto",
            "effect": {
                "action": "store_top_card_of_zone",
                "owner": "me",
                "zone": "deck",
                "position": "top",
                "store_as": "processione_top",
            },
        },
                {
                    "activation_mode": "mandatory_auto",
            "effect": {
                "action": "reveal_stored_card",
                "stored": "processione_top",
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {
                "stored_card_matches": {
                    "stored": "processione_top",
                    "card_filter": {
                        "card_type_in": ["Santo"],
                    },
                }
            },
            "effect": {
                "action": "move_stored_card_to_zone",
                "stored": "processione_top",
                "to_zone": "hand",
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {
                "stored_card_matches": {
                    "stored": "processione_top",
                    "card_filter": {
                        "card_type_in": ["Santo"],
                    },
                }
            },
            "effect": {
                "action": "move_source_to_zone",
                "to_zone": "hand",
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {
                "not": {
                    "stored_card_matches": {
                        "stored": "processione_top",
                        "card_filter": {
                            "card_type_in": ["Santo"],
                        },
                    }
                }
            },
            "effect": {
                "action": "move_stored_card_to_zone",
                "stored": "processione_top",
                "to_zone": "excommunicated",
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {
                "not": {
                    "stored_card_matches": {
                        "stored": "processione_top",
                        "card_filter": {
                            "card_type_in": ["Santo"],
                        },
                    }
                }
            },
            "effect": {
                "action": "move_source_to_zone",
                "to_zone": "excommunicated",
            },
        },
    ],
}
