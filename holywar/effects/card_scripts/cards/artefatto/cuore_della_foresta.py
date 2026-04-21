from __future__ import annotations

CARD_NAME = "Cuore della foresta"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_saint_defeated_in_battle",
                "frequency": "each_turn",
            },
            "condition": {
                "event_card_name_is": "Token Albero",
            },
            "target": {
                "type": "none",
            },
            "effect": {
                "action": "inflict_sin",
                "amount": 1,
                "target_player": "opponent",
            },
        }
    ],
    "on_play_actions": [],
}