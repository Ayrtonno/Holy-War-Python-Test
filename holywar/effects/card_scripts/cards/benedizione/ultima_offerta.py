from __future__ import annotations

CARD_NAME = 'Ultima Offerta'

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
                "zone": "hand",
                "owner": "me",
                "card_filter": {"card_type_in": ["santo"]},
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "store_target_strength", "flag": "ultima_offerta_discarded_strength"},
        },
        {
            "target": {
                "type": "selected_target",
            },
            "effect": {"action": "send_to_graveyard"},
        },
        {
            "target": {
                "type": "selected_target",
                "zone": "field",
                "owner": "me",
                "card_filter": {"card_type_in": ["santo", "token"]},
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "increase_faith_from_flag", "flag": "ultima_offerta_discarded_strength"},
        },
    ],
}
