from __future__ import annotations

CARD_NAME = """Pietre Aguzze"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_opponent_saint_enters_field", "frequency": "each_time"},
            "target": {"type": "none"},
            "effect": {"action": "inflict_sin", "amount": 2, "target_player": "opponent"},
        }
    ],
    "on_play_actions": [],
}