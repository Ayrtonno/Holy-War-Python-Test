from __future__ import annotations

CARD_NAME = 'Frammento dello Specchio'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "activate_once_per_turn": True,
    "activate_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [],
    "on_activate_actions": [
        {
            "effect": {
                "action": "excommunicate_top_cards_from_relicario",
                "target_player": "me",
                "amount": 1,
            }
        },
    ],
}
