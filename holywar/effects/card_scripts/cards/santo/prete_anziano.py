from __future__ import annotations

CARD_NAME = """Prete Anziano"""

SCRIPT = {
    "on_play_mode": "auto",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_this_card_attacks", "frequency": "each_turn"},
            "target": {"type": "source_card"},
            "effect": {
                "action": "remove_sin",
                "amount": 3,
                "target_player": "me",
            }
        }
    ],
    "on_play_actions": [],
}
