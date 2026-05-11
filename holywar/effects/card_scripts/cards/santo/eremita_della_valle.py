from __future__ import annotations

CARD_NAME = "Eremita della Valle"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [
        {
            "trigger": {"event": "on_this_card_destroyed", "frequency": "each_time"},
            "target": {"type": "source_card"},
            "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"},
        },
        {
            "trigger": {"event": "on_this_card_destroyed", "frequency": "each_time"},
            "target": {"type": "source_card"},
            "effect": {"action": "mill_cards", "amount": 1, "target_player": "opponent"},
        },
    ],
    "on_play_actions": [],
}
