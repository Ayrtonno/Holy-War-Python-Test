from __future__ import annotations

CARD_NAME = "Creature del Sottobosco"

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_this_card_leaves_field",
                "condition": {
                    "payload_to_zone_in": ["excommunicated"],
                },
            },
            "target": {"type": "source_card"},
            "effect": {
                "action": "draw_cards",
                "amount": 3,
                "target_player": "me",
            },
        }
    ],
    "on_play_actions": [],
}