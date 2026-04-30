from __future__ import annotations

CARD_NAME = 'Ptah'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [
        {
            "trigger": {"event": "on_main_phase_start", "frequency": "each_turn"},
            "condition": {
                "all_of": [
                    {"turn_scope": "my"},
                    {"source_on_field": True},
                    {"controller_drawn_cards_this_turn_gte": 1},
                ]
            },
            "target": {"type": "source_card"},
            "effect": {
                "action": "choose_option",
                "choice_title": "Ptah",
                "choice_prompt": "Vuoi rimettere una carta pescata questo turno nel reliquiario per pescarne un'altra?",
                "choice_options": [
                    {"value": "yes", "label": "Si"},
                    {"value": "no", "label": "No"},
                ],
            },
        },
        {
            "trigger": {"event": "on_main_phase_start", "frequency": "each_turn"},
            "condition": {
                "all_of": [
                    {"turn_scope": "my"},
                    {"source_on_field": True},
                    {"controller_drawn_cards_this_turn_gte": 1},
                    {"selected_option_in": ["yes"]},
                ]
            },
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "hand",
                "owner": "me",
                "card_filter": {"drawn_this_turn_only": True},
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "trigger": {"event": "on_main_phase_start", "frequency": "each_turn"},
            "condition": {
                "all_of": [
                    {"turn_scope": "my"},
                    {"source_on_field": True},
                    {"controller_drawn_cards_this_turn_gte": 1},
                    {"selected_option_in": ["yes"]},
                ]
            },
            "target": {
                "type": "selected_target",
            },
            "effect": {"action": "move_to_relicario"},
        },
        {
            "trigger": {"event": "on_main_phase_start", "frequency": "each_turn"},
            "condition": {
                "all_of": [
                    {"turn_scope": "my"},
                    {"source_on_field": True},
                    {"controller_drawn_cards_this_turn_gte": 1},
                    {"selected_option_in": ["yes"]},
                ]
            },
            "target": {"type": "source_card"},
            "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"},
        },
    ],
    "on_play_actions": [
        {"effect": {"action": "draw_cards", "amount": 0, "target_player": "me"}},
    ],
}
