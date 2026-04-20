from __future__ import annotations

CARD_NAME = "Rito Funebre"

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
                "owner": "any",
                "card_filter": {
                    "card_type_in": ["santo"],
                },
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {
                "action": "move_to_relicario",
            },
        },
        {
            "target": {
                "type": "selected_target",
            },
            "effect": {
                "action": "shuffle_target_owner_decks",
            },
        },
    ],
}
