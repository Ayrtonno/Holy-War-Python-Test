from __future__ import annotations

CARD_NAME = """Sequoia"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_this_card_kills_in_battle", "frequency": "each_turn"},
            "target": {"type": "event_card"},
            "effect": {"action": "double_strength"},
        }
    ],
    "on_play_actions": [],
}

