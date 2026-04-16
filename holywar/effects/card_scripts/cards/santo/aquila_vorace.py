from __future__ import annotations

CARD_NAME = "Aquila Vorace"

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_this_card_kills_in_battle",
                "frequency": "each_turn",
            },
            "target": {"type": "event_card"},
            "effect": {
                "action": "return_to_hand",
                "once_per_turn_group": "aquila_vorace_return",
            }
        }
    ],
    "on_play_actions": [],
}
