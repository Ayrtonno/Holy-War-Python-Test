from __future__ import annotations

CARD_NAME = "Memoria della Pietra"

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
                "card_filter": {
                    "name_contains": "Pietra",
                    "card_type_in": ["santo", "token"],
                },
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {
                "action": "summon_named_card",
            },
        },
        {
            "target": {
                "type": "source_card",
            },
            "effect": {
                "action": "excommunicate_card",
            },
        },
    ],
}
