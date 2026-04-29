from __future__ import annotations

CARD_NAME = "Mummificazione Prematura"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "guided",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "selected_target",
                "zone": "deck",
                "owner": "me",
                "card_filter": {
                    "card_type_in": ["santo"],
                },
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {
                "action": "remove_sin_equal_to_target_faith_and_strength",
                "target_player": "me",
            },
        },
        {
            "target": {
                "type": "selected_target",
                "zone": "deck",
                "owner": "me",
                "card_filter": {
                    "card_type_in": ["santo"],
                },
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {
                "action": "send_to_graveyard",
            },
        },
    ],
}
