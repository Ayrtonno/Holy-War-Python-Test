from __future__ import annotations

CARD_NAME = "Mutazione Divina"

ELEMENT_ARTIFACTS = ["Terra", "Aria", "Fuoco", "Acqua"]

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
                "card_filter": {
                    "card_type_in": ["artefatto"],
                    "name_in": ELEMENT_ARTIFACTS,
                },
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "send_to_graveyard"},
        },
        {
            "target": {
                "type": "selected_target",
                "owner": "me",
                "zone": "hand",
                "card_filter": {
                    "card_type_in": ["artefatto"],
                    "name_in": ELEMENT_ARTIFACTS,
                },
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "summon_card_from_hand"},
        },
    ],
}
