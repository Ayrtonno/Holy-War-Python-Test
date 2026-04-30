from __future__ import annotations

CARD_NAME = 'Ritorno Infame'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "selected_target",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {
                    "card_type_in": ["santo"],
                    "crosses_lte": 7,
                },
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "summon_target_to_field"},
        },
        {
            "target": {
                "type": "selected_target",
            },
            "effect": {"action": "prevent_specific_card_from_attacking", "amount": 1},
        },
    ],
}
