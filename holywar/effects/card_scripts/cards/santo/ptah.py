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
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "hand",
                "owner": "me",
                "card_filter": {"drawn_this_turn_only": True},
                "max_targets": 1,
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
                ]
            },
            "target": {"type": "source_card"},
            "effect": {"action": "shuffle_deck", "target_player": "me"},
        },
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
            "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"},
        },
    ],
    "on_play_actions": [
        {"effect": {"action": "draw_cards", "amount": 0, "target_player": "me"}},
    ],
}
