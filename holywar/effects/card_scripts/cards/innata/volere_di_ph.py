from __future__ import annotations

CARD_NAME = """Volere di Ph"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_card_drawn",
                "frequency": "each_time",
                "condition": {"event_card_owner": "me"},
            },
            "target": {"type": "source_card"},
            "effect": {"action": "inflict_sin", "amount": 1, "target_player": "me"},
        },
        {
            "trigger": {
                "event": "on_card_excommunicated",
                "frequency": "each_time",
            },
            "target": {"type": "source_card"},
            "effect": {"action": "remove_sin", "amount": 1, "target_player": "me"},
        },
    ],
    "on_play_actions": [],
}
