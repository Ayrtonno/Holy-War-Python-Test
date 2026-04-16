from __future__ import annotations

CARD_NAME = """Albero Secolare"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_this_card_receives_damage", "frequency": "each_turn"},
            "condition": {"target_current_faith_gte": 1},
            "target": {"type": "event_card"},
            "effect": {"action": "increase_faith", "amount": 7},
        }
    ],
    "on_play_actions": [],
}

