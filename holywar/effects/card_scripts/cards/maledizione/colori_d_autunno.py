from __future__ import annotations

CARD_NAME = "Colori d'Autunno"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {
                    "name_contains": "Albero",
                },
            },
            "effect": {
                "action": "store_target_count",
                "flag": "_colori_autunno_tree_count",
            },
        },
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {
                    "name_contains": "Albero",
                },
            },
            "effect": {
                "action": "inflict_sin_to_target_owners",
                "amount": 2,
            },
        },
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {
                    "name_contains": "Albero",
                },
            },
            "effect": {
                "action": "destroy_card",
            },
        },
        {
            "target": {"type": "source_card"},
            "effect": {
                "action": "summon_named_card_from_flag",
                "card_name": "Segno Del Passato",
                "flag": "_colori_autunno_tree_count",
            },
        },
    ],
}
