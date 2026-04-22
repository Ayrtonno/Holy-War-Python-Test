from __future__ import annotations

CARD_NAME = """Ciclicità Climatica"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "activate_once_per_turn": True,
    "activate_targeting": "guided",
    "triggered_effects": [],
    "on_play_actions": [],
    "on_activate_actions": [
        {
            "target": {
                "type": "selected_target",
                "owner": "me",
                "zone": "graveyard",
                "card_filter": {"card_type_in": ["santo", "token"], "crosses_lte": 4},
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "summon_target_to_field"},
        }
    ],
}
