from __future__ import annotations

CARD_NAME = """Larva Pestilenziale"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_this_card_destroyed",
                "frequency": "each_turn",
                "condition": {"payload_reason_in": ["battle"]},
            },
            "target": {"type": "event_source_card"},
            "effect": {"action": "halve_strength_rounded_down"},
        }
    ],
    "on_play_actions": [],
}
