from __future__ import annotations

CARD_NAME = 'Giorno 4: Stelle'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {"type": "source_card"},
            "effect": {"action": "draw_matching_from_top_n", "amount": 3, "card_name": "Giorno", "target_player": "me"},
        },
    ],
}
