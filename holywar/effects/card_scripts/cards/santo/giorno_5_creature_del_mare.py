from __future__ import annotations

CARD_NAME = """Giorno 5: Creature del Mare"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_this_card_deals_damage", "frequency": "each_time"},
            "target": {"type": "source_card"},
            "effect": {"action": "increase_faith", "amount": 2},
        },
        {
            "trigger": {"event": "on_this_card_deals_damage", "frequency": "each_time"},
            "target": {"type": "source_card"},
            "effect": {"action": "increase_strength", "amount": 3},
        },
    ],
    "on_play_actions": [],
}
