from __future__ import annotations

CARD_NAME = "Veggente dell'Apocalisse"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "scripted",
    "on_activate_mode": "scripted",
    "play_targeting": "none",
    "activate_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {"effect": {"action": "draw_cards", "amount": 0, "target_player": "me"}},
    ],
    "on_enter_actions": [
        {
            "condition": {"controller_has_card_in_deck_with_name": "Sigillo"},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "deck",
                "owner": "me",
                "card_filter": {"name_contains": "Sigillo"},
                "max_targets": 1,
            },
            "effect": {"action": "move_to_hand"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "shuffle_deck", "target_player": "me"},
        },
    ],
    "on_activate_actions": [
        {
            "target": {"type": "source_card"},
            "effect": {
                "action": "choose_option",
                "choice_title": "Veggente dell'Apocalisse",
                "choice_prompt": "Scegli la modalità di attivazione.",
                "choice_options": [
                    {
                        "value": "add",
                        "label": "Aggiungi 1 Segnalino Sigillo",
                        "condition": {"controller_has_building_with_name": "Altare dei Sette Sigilli"},
                    },
                    {
                        "value": "draw",
                        "label": "Rimuovi 3 Segnalini e pesca 1 carta",
                        "condition": {
                            "all_of": [
                                {"controller_has_building_with_name": "Altare dei Sette Sigilli"},
                                {"controller_altare_sigilli_gte": 3},
                            ]
                        },
                    },
                ],
            },
        },
        {
            "condition": {
                "all_of": [
                    {"selected_option_in": ["add"]},
                    {"controller_has_building_with_name": "Altare dei Sette Sigilli"},
                ]
            },
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"name_contains": "Altare dei Sette Sigilli"},
                "max_targets": 1,
            },
            "effect": {"action": "add_seal_counter", "amount": 1},
        },
        {
            "condition": {
                "all_of": [
                    {"selected_option_in": ["draw"]},
                    {"controller_has_building_with_name": "Altare dei Sette Sigilli"},
                    {"controller_altare_sigilli_gte": 3},
                ]
            },
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"name_contains": "Altare dei Sette Sigilli"},
                "max_targets": 1,
            },
            "effect": {"action": "remove_seal_counter", "amount": 3},
        },
        {
            "condition": {
                "all_of": [
                    {"selected_option_in": ["draw"]},
                    {"controller_has_building_with_name": "Altare dei Sette Sigilli"},
                    {"controller_altare_sigilli_gte": 3},
                ]
            },
            "target": {"type": "source_card"},
            "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"},
        },
    ],
}