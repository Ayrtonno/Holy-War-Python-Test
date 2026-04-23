from __future__ import annotations

CARD_NAME = 'Veggenza'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {"type": "source_card"},
            "effect": {"action": "optional_draw_from_top_n_then_shuffle", "amount": 5, "target_player": "me"},
        },
    ],
}
