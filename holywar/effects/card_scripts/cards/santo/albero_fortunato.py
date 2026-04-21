from __future__ import annotations

CARD_NAME = "Albero Fortunato"

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_this_card_leaves_field",
            },
            "condition": {
                "payload_to_zone_in": ["graveyard"],
            },
            "target": {
                "type": "source_card",
            },
            "effect": {
                "action": "draw_cards",
                "amount": 2,
                "target_player": "me",
            },
        }
    ],
    "on_play_actions": [],
}