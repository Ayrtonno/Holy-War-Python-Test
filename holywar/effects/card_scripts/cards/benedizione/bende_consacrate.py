from __future__ import annotations

CARD_NAME = "Bende Consacrate"

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
                "owner": "me",
                "zone": "field",
                "card_filter": {"card_type_in": ["santo", "token"]},
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "equip_card"},
        },
        {
            "target": {"type": "equipped_target_of_source"},
            "effect": {"action": "grant_blessed_tag_from_source", "flag": "bende_consacrate"},
        },
    ],
}
