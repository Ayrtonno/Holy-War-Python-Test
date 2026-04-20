from __future__ import annotations

CARD_NAME = "Perdono"

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
                "zone": "excommunicated",
                "owner": "me",
                "min_targets": 1,
                "max_targets": 1,
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
            "target": {
                "type": "source_card",
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
    ],
}