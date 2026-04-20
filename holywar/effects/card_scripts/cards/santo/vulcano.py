from __future__ import annotations

CARD_NAME = "Vulcano"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "activate_once_per_turn": True,
    "can_play_from_hand": False,
    "activate_targeting": "board_card",
    "triggered_effects": [],
    "on_play_actions": [],
    "on_activate_actions": [
        {
            "target": {
                "type": "selected_target",
                "zone": "field",
                "owner": "any",
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {
                "action": "destroy_card",
            },
        },
    ],
}
