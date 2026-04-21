from __future__ import annotations

CARD_NAME = "Bifrost"

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
                "owner": "any",
                "card_filter": {
                    "card_type_in": ["santo", "token"],
                },
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {
                "action": "store_target_faith_and_excommunicate_no_sin",
                "flag": "bifrost_target_faith",
            },
        },
        {
            "target": {
                "type": "source_card",
            },
            "effect": {
                "action": "inflict_sin_from_flag",
                "flag": "bifrost_target_faith",
                "target_player": "opponent",
            },
        },
    ],
}
