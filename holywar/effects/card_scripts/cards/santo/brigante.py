from __future__ import annotations

CARD_NAME = """Brigante"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "play_requirements": {
        "can_play_by_sacrificing": {
            "owner": "me",
            "zone": "field",
            "card_filter": {"card_type_in": ["santo"]},
            "count": 1,
        },
        "choose_play_sacrifices_from_target": True,
        "play_sacrifices_no_sin_on_death": True,
        "gain_faith_from_play_sacrifices": True,
        "grant_no_sin_on_death_if_gained_faith_from_sacrifices": True,
    },
    "triggered_effects": [],
    "on_play_actions": [],
}
