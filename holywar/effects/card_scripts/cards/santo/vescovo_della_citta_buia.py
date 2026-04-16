from __future__ import annotations

CARD_NAME = "Vescovo della Città Buia"

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "scripted",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [],
    "on_enter_actions": [
        {
            "target": {"type": "source_card"},
            "effect": {"action": "increase_faith_per_opponent_saints", "amount": 5},
        }
    ],
}
