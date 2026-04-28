from __future__ import annotations

CARD_NAME = 'Settimo Sigillo: Apocalisse'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "play_requirements": {
        "all_of": [
            {"controller_has_building_matching": {"card_filter": {"script_is_altare_sigilli": True}}},
            {"controller_altare_sigilli_gte": 7},
        ]
    },
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {"type": "all_saints_on_field"},
            "effect": {"action": "remove_from_board_no_sin"},
        },
    ],
}
