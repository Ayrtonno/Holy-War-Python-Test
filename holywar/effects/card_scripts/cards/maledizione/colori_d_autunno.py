from __future__ import annotations

CARD_NAME = "Colori d'Autunno"

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {
                    "name_contains": "Albero",
                },
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {
                "action": "store_target_count",
                "flag": "_colori_autunno_tree_count",
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {
                    "name_contains": "Albero",
                },
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {
                "action": "inflict_sin_to_target_owners",
                "amount": 2,
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {
                    "name_contains": "Albero",
                },
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {
                "action": "destroy_card",
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "source_card",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {
                "action": "summon_named_card_from_flag",
                "placement_policy": "prompt_slot_required",
                "card_name": "Segno Del Passato",
                "flag": "_colori_autunno_tree_count",
            },
        },
    ],
}
