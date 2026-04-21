from __future__ import annotations

CARD_NAME = """Sabbie Mobili"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_attack_declared", "frequency": "each_time"},
            "condition": {"event_card_owner_attack_count_gte": 1},
            "target": {"type": "event_card"},
            "effect": {"action": "prevent_specific_card_from_attacking", "amount": 1},
        }
    ],
    "on_play_actions": [],
}
