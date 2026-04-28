from __future__ import annotations

CARD_NAME = 'Rituale Sepolcrale'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "guided",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "selected_target",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {"card_type_in": ["santo"]},
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "move_to_hand"},
        },
        {
            "target": {
                "type": "selected_target",
                "zone": "hand",
                "owner": "me",
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "move_to_graveyard"},
        },
    ],
}
