from __future__ import annotations

CARD_NAME = """Hun-Came"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "scripted",
    "on_activate_mode": "auto",
    "counted_bonuses": [],
    "faith_bonus_rules": [],
    "on_enter_actions": [
        {
            "target": {"type": "source_card"},
            "effect": {
                "action": "increase_source_stats_from_zone_count_div",
                "target_player": "me",
                "zone": "graveyard",
                "threshold": 5,
                "divisor": 5,
                "amount": 2,
            },
        }
    ],
    "triggered_effects": [],
    "on_play_actions": [],
}
