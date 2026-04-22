from __future__ import annotations

CARD_NAME = "Albero Fortunato"

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_card_sent_to_graveyard",
            },
            "condition": {
                "event_card_name_is": "Albero Fortunato",
                "event_card_owner": "me",
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
