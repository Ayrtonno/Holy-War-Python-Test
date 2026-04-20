from __future__ import annotations

CARD_NAME = "Passaggio all'Aldilà"

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
                "zone": "field",
                "owner": "me",
                "card_filter": {
                    "card_type_in": ["santo"],
                },
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {
                "action": "store_target_strength",
                "flag": "_passaggio_aldila_strength",
            },
        },
        {
            "target": {
                "type": "selected_target",
                "zone": "field",
                "owner": "me",
                "card_filter": {
                    "card_type_in": ["santo"],
                },
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {
                "action": "destroy_card",
            },
        },
        {
            "effect": {
                "action": "add_temporary_inspiration_from_flag",
                "flag": "_passaggio_aldila_strength",
                "target_player": "me",
            },
        },
    ],
}