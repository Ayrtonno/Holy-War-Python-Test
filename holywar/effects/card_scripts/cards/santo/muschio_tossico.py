from __future__ import annotations

CARD_NAME = "Muschio Tossico"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_this_card_destroyed",
                "frequency": "each_turn",
            },
            "target": {
                "type": "selected_target",
                "zone": "deck",
                "owner": "opponent",
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {
                "action": "send_to_graveyard",
            },
        }
    ],
    "on_play_actions": [],
}