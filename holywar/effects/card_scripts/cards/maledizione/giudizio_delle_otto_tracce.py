from __future__ import annotations

CARD_NAME = "Giudizio delle Otto Tracce"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "auto",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "effect": {
                "action": "store_distinct_count",
                "flag": "gd8_max_targets",
                "requirement": {
                    "zones": ["hand", "field", "graveyard"],
                    "owner": "me",
                    "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
                },
            }
        },
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "opponent",
                "card_filter": {"card_type_in": ["santo", "token", "artefatto", "edificio"]},
            },
            "effect": {"action": "choose_targets", "min_targets": 0, "max_targets": 8, "flag": "gd8_max_targets"},
        },
        {
            "target": {
                "type": "selected_targets",
            },
            "effect": {"action": "store_target_count", "flag": "gd8_destroyed_count"},
        },
        {
            "target": {
                "type": "selected_targets",
            },
            "effect": {"action": "destroy_card"},
        },
        {"effect": {"action": "inflict_sin_from_flag_scaled", "flag": "gd8_destroyed_count", "amount": 5, "target_player": "opponent"}},
        {"effect": {"action": "remove_sin_from_flag_scaled", "flag": "gd8_destroyed_count", "amount": 3, "target_player": "me"}},
    ],
}
