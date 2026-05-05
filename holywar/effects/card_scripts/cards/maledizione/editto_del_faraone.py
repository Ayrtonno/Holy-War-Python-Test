from __future__ import annotations

CARD_NAME = "Editto del Faraone"

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
                "zone": "field",
                "owner": "opponent",
                "card_filter": {"card_type_in": ["artefatto", "edificio"]},
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "send_to_graveyard"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "inflict_sin", "amount": 3, "target_player": "me"},
        },
    ],
}

