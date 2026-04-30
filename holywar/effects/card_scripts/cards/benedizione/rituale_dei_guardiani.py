from __future__ import annotations

CARD_NAME = 'Rituale dei Guardiani'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "guided",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "selected_target",
                "zone": "field",
                "owner": "me",
                "min_targets": 1,
                "max_targets": 1,
                "card_filter": {"card_type_in": ["santo"]},
            },
            "effect": {"action": "move_to_graveyard"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {
                "action": "store_top_card_of_zone",
                "owner": "me",
                "zone": "hand",
                "position": "top",
                "store_as": "rituale_guardiani_drawn",
            },
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "reveal_stored_card", "stored": "rituale_guardiani_drawn"},
        },
        {
            "condition": {
                "stored_card_matches": {
                    "stored": "rituale_guardiani_drawn",
                    "card_filter": {"card_type_in": ["santo"]},
                }
            },
            "target": {"type": "source_card"},
            "effect": {"action": "summon_stored_card_to_field", "stored": "rituale_guardiani_drawn"},
        },
        {
            "condition": {
                "not": {
                    "stored_card_matches": {
                        "stored": "rituale_guardiani_drawn",
                        "card_filter": {"card_type_in": ["santo"]},
                    }
                }
            },
            "target": {"type": "source_card"},
            "effect": {"action": "move_stored_card_to_zone", "stored": "rituale_guardiani_drawn", "to_zone": "graveyard"},
        },
    ],
}
