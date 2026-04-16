from __future__ import annotations

CARD_NAME = """Paladino della Fede"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "scripted",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "on_play_actions": [],
    "on_enter_actions": [
        {
            "effect": {"action": "swap_attack_defense"},
        }
    ],
}
