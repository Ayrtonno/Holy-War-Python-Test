from __future__ import annotations

CARD_NAME = "Mummificazione Prematura"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "auto",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "deck",
                "owner": "me",
                "card_filter": {
                    "card_type_in": ["santo"],
                },
            },
            "effect": {
                "action": "choose_targets",
                "min_targets": 1,
                "max_targets": 1,
            },
        },
        {
            "target": {
                "type": "selected_target",
            },
            "effect": {
                "action": "remove_sin_equal_to_target_faith_and_strength",
                "target_player": "me",
            },
        },
        {
            "target": {
                "type": "selected_target",
            },
            "effect": {
                "action": "send_to_graveyard",
            },
        },
    ],
}
