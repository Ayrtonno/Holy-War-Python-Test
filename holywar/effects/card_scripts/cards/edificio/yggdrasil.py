from __future__ import annotations

CARD_NAME = """Yggdrasil"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "scripted",
    "on_activate_mode": "scripted",
    "play_targeting": "none",
    "activate_targeting": "yggdrasil",
    "triggered_effects": [],
    "on_play_actions": [],
    "on_enter_actions": [
        {
            "condition": {"controller_has_card_in_deck_with_name": "Thor"},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "deck",
                "owner": "me",
                "card_filter": {"name_contains": "Thor"},
                "max_targets": 1,
            },
            "effect": {"action": "move_to_hand"},
        },
        {
            "condition": {"controller_has_card_in_deck_with_name": "Odino"},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "deck",
                "owner": "me",
                "card_filter": {"name_contains": "Odino"},
                "max_targets": 1,
            },
            "effect": {"action": "move_to_hand"},
        },
        {
            "condition": {"controller_has_card_in_deck_with_name": "Loki"},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "deck",
                "owner": "me",
                "card_filter": {"name_contains": "Loki"},
                "max_targets": 1,
            },
            "effect": {"action": "move_to_hand"},
        },
    ],
    "on_activate_actions": [
        {
            "condition": {"selected_target_startswith": "buff:"},
            "target": {"type": "selected_target"},
            "effect": {"action": "increase_faith", "amount": 2},
        },
        {
            "condition": {"selected_target_startswith": "buff:"},
            "target": {"type": "selected_target"},
            "effect": {"action": "increase_strength", "amount": 2},
        },
        {
            "condition": {"selected_target_in": ["artifact"]},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {"card_type_in": ["artefatto"]},
                "max_targets": 1,
            },
            "effect": {"action": "move_to_hand"},
        },
        {
            "condition": {
                "all_of": [
                    {"selected_target_in": ["draw"]},
                    {"controller_has_distinct_saints_gte": 3},
                ]
            },
            "target": {"type": "source_card"},
            "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"},
        },
        {
            "condition": {
                "all_of": [
                    {"selected_target_in": ["warcry"]},
                    {"controller_has_saint_with_name": "Thor"},
                    {"controller_has_saint_with_name": "Odino"},
                ]
            },
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"card_type_in": ["santo", "token"]},
            },
            "effect": {"action": "increase_strength", "amount": 1},
        },
    ],
}
