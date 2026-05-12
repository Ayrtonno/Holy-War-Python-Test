from __future__ import annotations

CARD_NAME = "Han Xiangzi"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "effect": {
                "action": "draw_cards_and_store_last_drawn",
                "amount": 1,
                "target_player": "me",
                "store_as": "han_draw_1",
            },
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "reveal_stored_card", "stored": "han_draw_1"},
        },
        {
            "condition": {
                "stored_card_matches": {
                    "stored": "han_draw_1",
                    "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
                }
            },
            "effect": {
                "action": "draw_cards_and_store_last_drawn",
                "amount": 1,
                "target_player": "me",
                "store_as": "han_draw_2",
            },
        },
        {
            "condition": {
                "stored_card_matches": {
                    "stored": "han_draw_1",
                    "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
                }
            },
            "target": {"type": "source_card"},
            "effect": {"action": "reveal_stored_card", "stored": "han_draw_2"},
        },
        {
            "condition": {
                "stored_card_matches": {
                    "stored": "han_draw_1",
                    "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
                }
            },
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "hand",
                "owner": "me",
                "max_targets": 1,
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "condition": {
                "all_of": [
                    {
                        "stored_card_matches": {
                            "stored": "han_draw_1",
                            "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
                        }
                    },
                    {"selected_target_exists": True},
                ]
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
