from __future__ import annotations

CARD_NAME = "Dono di Kah"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "effect": {
                "action": "draw_cards_and_set_play_cost_for_drawn_until_turn_end",
                "target_player": "me",
                "amount": 5,
                "override_cost": 2,
            }
        },
    ],
}
