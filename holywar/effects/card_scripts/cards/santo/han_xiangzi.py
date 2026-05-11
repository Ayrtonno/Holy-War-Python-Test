from __future__ import annotations

CARD_NAME = "Han Xiangzi"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "guided",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "effect": {
                "action": "draw_cards_and_store_last_drawn",
                "amount": 1,
                "target_player": "me",
                "store_as": "han_last_drawn",
            },
        },
        {
            "condition": {
                "stored_card_matches": {
                    "stored": "han_last_drawn",
                    "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
                }
            },
            "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"},
        },
        {
            "condition": {
                "stored_card_matches": {
                    "stored": "han_last_drawn",
                    "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
                }
            },
            "target": {
                "type": "selected_target",
                "zone": "hand",
                "owner": "me",
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "send_to_graveyard"},
        },
    ],
}
