from __future__ import annotations

CARD_NAME = "Risveglio di Ph-Dak'Gaph"

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
                "max_targets": 5,
            },
            "effect": {
                "action": "move_to_hand",
            },
        },
        {
            "effect": {
                "action": "remove_sin",
                "amount": 10,
                "target_player": "me",
            },
        },
        {
            "effect": {
                "action": "move_source_to_zone",
                "to_zone": "excommunicated",
            },
        },
    ],
}
