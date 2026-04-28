from __future__ import annotations

CARD_NAME = 'Arca della salvezza'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "guided",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "selected_targets",
                "zone": "field",
                "owner": "any",
                "card_filter": {"card_type_in": ["santo", "token"]},
                "min_targets": 2,
                "max_targets": 2,
            },
            "effect": {"action": "destroy_all_saints_except_selected", "min_targets": 2},
        }
    ],
}
