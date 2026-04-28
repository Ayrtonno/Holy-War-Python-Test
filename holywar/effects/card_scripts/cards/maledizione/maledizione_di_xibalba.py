from __future__ import annotations

CARD_NAME = 'Maledizione di Xibalba'

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
            "effect": {"action": "store_target_count", "flag": "xibalba_grave_count"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "floor_divide_flag", "flag": "xibalba_grave_count", "amount": 5},
        },
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "opponent",
                "card_filter": {"card_type_in": ["santo", "token"]},
            },
            "effect": {"action": "decrease_faith_from_flag", "flag": "xibalba_grave_count"},
        },
    ],
}
