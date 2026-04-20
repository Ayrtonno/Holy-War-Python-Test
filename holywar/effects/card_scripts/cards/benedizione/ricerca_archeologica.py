from __future__ import annotations

CARD_NAME = "Ricerca Archeologica"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "selected_target",
                "zone": "relicario",
                "owner": "me",
                "card_filter": {
                    "card_type_in": ["artefatto"],
                },
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {
                "action": "move_to_hand",
            },
        },
        {
            "effect": {
                "action": "shuffle_deck",
                "target_player": "me",
            },
        },
    ],
}
