from __future__ import annotations

CARD_NAME = 'Proibizione Naturale'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "play_targeting": "guided",
    "on_play_actions": [
        {
            "target": {
                "type": "selected_target",
                "owner": "opponent",
                "zone": "field",
                "card_filter": {"card_type_in": ["santo", "token"]},
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "prevent_specific_card_from_activating", "amount": 1},
        }
    ],
}
