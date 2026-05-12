from __future__ import annotations

CARD_NAME = "Veggente dell'Apocalisse"

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "scripted",
    "on_activate_mode": "scripted",
    "activate_once_per_turn": True,
    "play_targeting": "none",
    "activate_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [],
    "on_enter_actions": [
        {
            "activation_mode": "mandatory_auto",
            "condition": {
                "controller_has_cards": {
                    "owner": "me",
                    "zone": "deck",
                    "card_filter": {"name_contains": "Sigillo"},
                    "min_count": 1,
                }
            },
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "deck",
                "owner": "me",
                "card_filter": {"name_contains": "Sigillo"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "choose_targets", "min_targets": 0, "max_targets": 1},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {
                "all_of": [
                    {
                        "controller_has_cards": {
                            "owner": "me",
                            "zone": "deck",
                            "card_filter": {"name_contains": "Sigillo"},
                            "min_count": 1,
                        }
                    },
                    {"selected_target_exists": True},
                ]
            },
            "target": {
                "type": "selected_target",
                "zone": "deck",
                "owner": "me",
                "card_filter": {"name_contains": "Sigillo"},
                "min_targets": 1,
                "max_targets": 1,
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "move_to_hand"},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {"selected_target_exists": True},
            "target": {"type": "source_card"},
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "shuffle_deck", "target_player": "me"},
        },
    ],
    "on_activate_actions": [
        {
            "activation_mode": "mandatory_auto",
            "target": {"type": "source_card"},
            "effect": {
                "action": "choose_option",
                "choice_title": "Veggente dell'Apocalisse",
                "choice_prompt": "Scegli la modalità di attivazione.",
                "choice_options": [
                    {
                        "value": "add",
                        "label": "Aggiungi 1 Segnalino Sigillo",
                        "condition": {"controller_has_building_matching": {"card_filter": {"script_is_altare_sigilli": True}}},
                    },
                    {
                        "value": "draw",
                        "label": "Rimuovi 3 Segnalini e pesca 1 carta",
                        "condition": {
                            "all_of": [
                                {"controller_has_building_matching": {"card_filter": {"script_is_altare_sigilli": True}}},
                                {"controller_altare_sigilli_gte": 3},
                            ]
                        },
                    },
                ],
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {
                "all_of": [
                    {"selected_option_in": ["add"]},
                    {"controller_has_building_matching": {"card_filter": {"script_is_altare_sigilli": True}}},
                ]
            },
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"script_is_altare_sigilli": True},
                "max_targets": 1,
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "add_seal_counter", "amount": 1},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {
                "all_of": [
                    {"selected_option_in": ["draw"]},
                    {"controller_has_building_matching": {"card_filter": {"script_is_altare_sigilli": True}}},
                    {"controller_altare_sigilli_gte": 3},
                ]
            },
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"script_is_altare_sigilli": True},
                "max_targets": 1,
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "remove_seal_counter", "amount": 3},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {
                "all_of": [
                    {"selected_option_in": ["draw"]},
                    {"controller_has_building_matching": {"card_filter": {"script_is_altare_sigilli": True}}},
                    {"controller_altare_sigilli_gte": 3},
                ]
            },
            "target": {"type": "source_card"},
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"},
        },
    ],
}
