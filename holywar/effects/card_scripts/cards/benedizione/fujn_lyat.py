from __future__ import annotations

CARD_NAME = "Fujn'lyat"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "guided",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "selected_targets",
                "zone": "graveyard",
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
    ],
}