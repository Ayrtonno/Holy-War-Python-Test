from __future__ import annotations

CARD_NAME = """Token Sacrificale"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_this_card_destroyed", "frequency": "each_turn"},
            "target": {"type": "source_card"},
            "effect": {"action": "inflict_sin_to_event_controller", "amount": 5},
        }
    ],
    "on_play_actions": [],
}
