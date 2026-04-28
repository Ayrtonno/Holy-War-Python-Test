from __future__ import annotations

CARD_NAME = """Anima Errante"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_this_card_leaves_field", "frequency": "each_time"},
            "target": {"type": "source_card"},
            "effect": {
                "action": "summon_generated_token",
                "card_name": "Token Spirito Vacuo",
            },
        }
    ],
    "on_play_actions": [],
}
