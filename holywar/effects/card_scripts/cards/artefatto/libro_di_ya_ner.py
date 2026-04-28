from __future__ import annotations

CARD_NAME = "Libro di Ya-ner"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "activate_once_per_turn": True,
    "activate_targeting": "none",
    "play_requirements": {
        "not": {
            "controller_has_cards": {
                "owner": "me",
                "zones": ["artifacts"],
                "card_filter": {"name_equals": "Libro di Ya-ner"},
                "min_count": 2,
            }
        }
    },
    "triggered_effects": [
        {
            "trigger": {"event": "on_this_card_leaves_field", "frequency": "each_time"},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"card_type_in": ["token"], "name_contains": "Gub-ner"},
            },
            "effect": {"action": "store_target_count", "flag": "libro_ya_ner_token_count_a"},
        },
        {
            "trigger": {"event": "on_this_card_leaves_field", "frequency": "each_time"},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"card_type_in": ["token"], "name_contains": "Gub-ner"},
            },
            "effect": {"action": "store_target_count", "flag": "libro_ya_ner_token_count_b"},
        },
        {
            "trigger": {"event": "on_this_card_leaves_field", "frequency": "each_time"},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"card_type_in": ["token"], "name_contains": "Gub-ner"},
            },
            "effect": {"action": "destroy_card"},
        },
        {
            "trigger": {"event": "on_this_card_leaves_field", "frequency": "each_time"},
            "target": {"type": "source_card"},
            "effect": {
                "action": "remove_sin_from_flag",
                "flag": "libro_ya_ner_token_count_a",
                "target_player": "me",
            },
        },
        {
            "trigger": {"event": "on_this_card_leaves_field", "frequency": "each_time"},
            "target": {"type": "source_card"},
            "effect": {
                "action": "remove_sin_from_flag",
                "flag": "libro_ya_ner_token_count_b",
                "target_player": "me",
            },
        },
    ],
    "on_play_actions": [],
    "on_activate_actions": [
        {
            "target": {"type": "source_card"},
            "effect": {"action": "summon_generated_token", "card_name": "Token Gub-ner", "owner": "me"},
        }
    ],
}
