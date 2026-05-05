from __future__ import annotations

CARD_NAME = "Apparizione"

ELEMENT_ARTIFACTS = ["Terra", "Aria", "Fuoco", "Acqua"]

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "guided",
    "play_requirements": {
        "all_of": [
            {
                "controller_has_cards": {
                    "owner": "me",
                    "zone": "field",
                    "card_filter": {"name_equals": name},
                }
            }
            for name in ELEMENT_ARTIFACTS
        ]
    },
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "selected_target",
                "owner": "me",
                "zone": "relicario",
                "zones": ["relicario", "graveyard"],
                "card_filter": {
                    "name_equals": "Dio, il Creatore",
                    "card_type_in": ["santo"],
                },
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "move_to_hand"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "shuffle_deck", "target_player": "me"},
        },
    ],
}
