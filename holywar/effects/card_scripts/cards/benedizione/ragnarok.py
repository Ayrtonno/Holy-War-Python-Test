from __future__ import annotations

CARD_NAME = 'Ragnarok'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"card_type_in": ["santo", "token"]},
            },
            "effect": {"action": "store_target_count", "flag": "ragnarok_my_saints_destroyed"},
        },
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "any",
                "card_filter": {"card_type_in": ["santo", "token"]},
            },
            "effect": {"action": "send_to_graveyard"},
        },
        {
            "effect": {
                "action": "draw_cards_from_flag",
                "flag": "ragnarok_my_saints_destroyed",
                "target_player": "me",
            },
        },
        {
            "target": {
                "type": "selected_target",
                "owner": "me",
                "zones": ["hand"],
                "card_filter": {
                    "card_type_in": ["santo"],
                    "name_in": ["Fenrir", "Jormungandr"],
                },
                "min_targets": 0,
                "max_targets": 1,
            },
            "effect": {"action": "summon_target_to_field"},
        },
    ],
}
