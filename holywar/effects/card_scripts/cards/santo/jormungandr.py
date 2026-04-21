from __future__ import annotations

CARD_NAME = """Jormungandr"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_this_card_attacks"},
            "target": {"type": "source_card"},
            "effect": {"action": "increase_faith", "amount": 1},
        },
    ],
    "on_play_actions": [],
}
