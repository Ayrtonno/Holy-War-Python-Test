from __future__ import annotations

CARD_NAME = "Sacrificio della Fertilità"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "graveyard",
                "owner": "me",
            },
            "effect": {"action": "store_target_count", "flag": "sacrificio_fertilita_grave_count"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "floor_divide_flag", "flag": "sacrificio_fertilita_grave_count", "amount": 5},
        },
        {
            "target": {"type": "source_card"},
            "effect": {
                "action": "remove_sin_from_flag",
                "flag": "sacrificio_fertilita_grave_count",
                "target_player": "me",
            },
        },
    ],
}
