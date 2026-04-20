from __future__ import annotations

CARD_NAME = "Deriu-hebet"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "activate_once_per_turn": True,
    "activate_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [],
    "on_activate_actions": [
        {
            "effect": {
                "action": "store_top_card_of_zone",
                "owner": "me",
                "zone": "deck",
                "position": "top",
                "store_as": "deriu_top",
            },
        },
        {
            "effect": {
                "action": "reveal_stored_card",
                "stored": "deriu_top",
            },
        },
        {
            "condition": {
                "stored_card_matches": {
                    "stored": "deriu_top",
                    "card_filter": {
                        "card_type_in": ["Benedizione", "Maledizione"],
                    },
                }
            },
            "effect": {
                "action": "move_stored_card_to_zone",
                "stored": "deriu_top",
                "to_zone": "hand",
            },
        },
        {
            "condition": {
                "not": {
                    "stored_card_matches": {
                        "stored": "deriu_top",
                        "card_filter": {
                            "card_type_in": ["Benedizione", "Maledizione"],
                        },
                    }
                }
            },
            "effect": {
                "action": "shuffle_deck",
                "target_player": "me",
            },
        },
    ],
}
