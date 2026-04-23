from __future__ import annotations

CARD_NAME = "Dio, il Creatore"

ELEMENT_NAMES = ["Aria", "Fuoco", "Terra", "Acqua"]

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "play_requirements": {
        "all_of": [
            {
                "controller_has_cards": {
                    "zone": "field",
                    "owner": "me",
                    "card_filter": {"name_equals": name},
                }
            }
            for name in ELEMENT_NAMES
        ]
    },
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_saint_defeated_or_destroyed",
                "frequency": "each_turn",
                "condition": {
                    "all_of": [
                        {"event_card_owner": "opponent"},
                        {"event_card_type_in": ["santo", "token"]},
                    ]
                },
            },
            "target": {"type": "event_card"},
            "effect": {"action": "store_target_faith", "flag": "dio_creatore_removed_sin"},
        },
        {
            "trigger": {
                "event": "on_saint_defeated_or_destroyed",
                "frequency": "each_turn",
                "condition": {
                    "all_of": [
                        {"event_card_owner": "opponent"},
                        {"event_card_type_in": ["santo", "token"]},
                    ]
                },
            },
            "target": {"type": "source_card"},
            "effect": {"action": "remove_sin_from_flag", "flag": "dio_creatore_removed_sin", "target_player": "me"},
        },
    ],
    "on_play_actions": [
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"name_in": ELEMENT_NAMES},
            },
            "effect": {"action": "destroy_card"},
        }
    ],
}
