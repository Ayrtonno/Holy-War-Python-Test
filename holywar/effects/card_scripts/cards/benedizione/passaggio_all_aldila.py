from __future__ import annotations

CARD_NAME = "Passaggio all'Aldilà"

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
                "zone": "field",
                "owner": "me",
                "card_filter": {
                    "card_type_in": ["santo"],
                },
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "target": {
                "type": "selected_target",
            },
            "effect": {
                "action": "store_target_strength",
                "flag": "_passaggio_aldila_strength",
            },
        },
        {
            "target": {
                "type": "selected_target",
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
