from __future__ import annotations

CARD_NAME = "Legame Primordiale"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "guided",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "selected_targets",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {
                    "crosses_lte": 7,
                },
                "min_targets": 0,
                "max_targets_from": {
                    "count_cards_controlled_by_owner": {
                        "owner": "me",
                        "zone": "field",
                        "card_filter": {
                            "card_type_in": ["albero"],
                        },
                    }
                },
            },
            "effect": {
                "action": "move_to_relicario",
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