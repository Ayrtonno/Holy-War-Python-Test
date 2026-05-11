from __future__ import annotations

CARD_NAME = """Giorno 6: Creature di Terra"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_this_card_deals_damage", "frequency": "each_time"},
            "target": {"type": "source_card"},
            "effect": {"action": "increase_faith", "amount": 3},
        },
        {
            "trigger": {"event": "on_this_card_deals_damage", "frequency": "each_time"},
            "target": {"type": "source_card"},
            "effect": {"action": "increase_strength", "amount": 2},
        },
    ],
    "on_play_actions": [],
}
