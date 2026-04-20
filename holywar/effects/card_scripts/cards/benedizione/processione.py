from __future__ import annotations

CARD_NAME = "Processione"

SCRIPT = {
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
            "effect": {
                "action": "store_top_card_of_zone",
                "owner": "me",
                "zone": "deck",
                "position": "top",
                "store_as": "processione_top",
            },
        },
        {
            "effect": {
                "action": "reveal_stored_card",
                "stored": "processione_top",
            },
        },
        {
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