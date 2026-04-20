from __future__ import annotations

CARD_NAME = 'Uragano'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "on_play_actions": [{
            "target": {
                "type": "selected_target",
                "zone": "field",
                "owner": "opponent",
                "card_filter": {
                    "card_type_in": ["santo", "token"],
                },
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {
                "action": "destroy_card",
            },
        },
        {
            "target": {
                "type": "selected_target",
                "zone": "field",
                "owner": "opponent",
                "card_filter": {
                    "card_type_in": ["artefatto"],
                },
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {
                "action": "destroy_card",
            },
        },],
}