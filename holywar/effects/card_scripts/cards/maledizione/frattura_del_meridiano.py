from __future__ import annotations

CARD_NAME = "Frattura del Meridiano"

HAS_2_BAXIAN_FIELD = {
    "controller_has_cards": {
        "zones": ["field"],
        "owner": "me",
        "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
        "min_count": 2,
    }
}

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
            "effect": {"action": "destroy_card"},
        },
        {
            "condition": HAS_2_BAXIAN_FIELD,
            "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"},
        },
    ],
}
