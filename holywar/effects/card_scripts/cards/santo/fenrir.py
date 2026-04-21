from __future__ import annotations

CARD_NAME = """Fenrir"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_this_card_attacks", "condition": {"payload_target_slot_is_set": True}},
            "target": {"type": "source_card"},
            "effect": {"action": "increase_strength", "amount": 1},
        },
    ],
    "on_play_actions": [],
}
