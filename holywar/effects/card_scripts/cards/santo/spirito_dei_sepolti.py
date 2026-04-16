from __future__ import annotations

CARD_NAME = """Spirito dei Sepolti"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_this_card_leaves_field", "frequency": "each_turn"},
            "target": {
                "type": "all_saints_on_field",
                "card_filter": {"exclude_event_card": True},
            },
            "effect": {"action": "increase_faith", "amount": 1},
        },
        {
            "trigger": {"event": "on_this_card_leaves_field", "frequency": "each_turn"},
            "target": {
                "type": "all_saints_on_field",
                "card_filter": {"exclude_event_card": True},
            },
            "effect": {"action": "increase_strength", "amount": 2},
        }
    ],
    "on_play_actions": [],
}
