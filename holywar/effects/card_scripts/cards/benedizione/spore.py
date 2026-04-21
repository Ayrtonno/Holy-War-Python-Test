from __future__ import annotations

CARD_NAME = "Spore"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "owner": "me",
                "zone": "hand",
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
        {
            "effect": {
                "action": "set_next_turn_draw_override",
                "amount": 8,
                "target_player": "me",
            },
        },
    ],
}
