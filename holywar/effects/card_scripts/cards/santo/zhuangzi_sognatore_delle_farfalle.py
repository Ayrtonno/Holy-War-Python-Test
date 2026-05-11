from __future__ import annotations

CARD_NAME = "Zhuangzi, Sognatore delle Farfalle"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {"effect": {"action": "draw_cards", "amount": 1, "target_player": "me"}},
        {"effect": {"action": "draw_cards", "amount": 1, "target_player": "opponent"}},
        {
            "condition": {"controller_hand_size_equals_opponent": True},
            "target": {"type": "source_card"},
            "effect": {"action": "increase_strength", "amount": 2},
        },
    ],
}
