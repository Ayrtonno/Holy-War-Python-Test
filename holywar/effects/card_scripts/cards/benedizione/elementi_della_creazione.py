from __future__ import annotations

CARD_NAME = "Elementi della Creazione"

ELEMENT_ARTIFACTS = ["Terra", "Aria", "Fuoco", "Acqua"]

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "guided",
    "play_requirements": {
        "controller_free_artifact_slots_gte": 2,
    },
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "selected_targets",
                "owner": "me",
                "zone": "relicario",
                "zones": ["relicario", "graveyard"],
                "card_filter": {
                    "card_type_in": ["artefatto"],
                    "name_in": ELEMENT_ARTIFACTS,
                },
                "min_targets": 2,
                "max_targets": 2,
            },
            "effect": {"action": "summon_target_to_field"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "shuffle_deck", "target_player": "me"},
        },
    ],
}
