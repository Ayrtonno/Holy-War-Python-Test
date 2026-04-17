from __future__ import annotations

CARD_NAME = "Cronologia Sacra"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "hand",
                "owner": "me",
            },
            "effect": {
                "action": "send_to_graveyard",
            },
        },
        {
            "effect": {
                "action": "draw_cards",
                "amount": 5,
            },
        },
    ],
}