from __future__ import annotations

CARD_NAME = "Rito della Ri-Manifestazione"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "selected_targets",
                "zone": "excommunicated",
                "owner": "me",
                "min_targets": 1,
                "max_targets": 3,
            },
            "effect": {
                "action": "move_to_relicario",
            },
        },
        {
            "effect": {
                "action": "shuffle_deck",
                "target_player": "me",
            },
        },
        {
            "condition": {
                "any_of": [
                    {"controller_has_building_with_name": "Av'drna"},
                    {"controller_has_building_with_name": "Ph'drna"},
                ],
            },
            "effect": {
                "action": "draw_cards",
                "amount": 1,
                "target_player": "me",
            },
        },
    ],
}
