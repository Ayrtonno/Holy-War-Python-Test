from __future__ import annotations

CARD_NAME = """Piramide: Micerino"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "is_pyramid": True,
    "counted_bonuses": [
        {
            "context": "strength",
            "group": "pyramid_set_strength",
            "stacking": "max",
            "threshold": 1,
            "amount_mode": "flat",
            "amount": 5,
            "requirement": {
                "owner": "me",
                "zone": "artifacts",
                "card_filter": {"script_is_pyramid": True},
            },
        },
        {
            "context": "summon_faith",
            "group": "pyramid_set_summon_faith",
            "stacking": "max",
            "threshold": 2,
            "amount_mode": "base_faith_multiplier",
            "amount": 1,
            "requirement": {
                "owner": "me",
                "zone": "artifacts",
                "card_filter": {"script_is_pyramid": True},
            },
        },
        {
            "context": "turn_draw",
            "group": "pyramid_set_turn_draw",
            "stacking": "max",
            "threshold": 3,
            "amount_mode": "flat",
            "amount": 2,
            "requirement": {
                "owner": "me",
                "zone": "artifacts",
                "card_filter": {"script_is_pyramid": True},
            },
        },
    ],
    "triggered_effects": [],
    "on_play_actions": [],
}
