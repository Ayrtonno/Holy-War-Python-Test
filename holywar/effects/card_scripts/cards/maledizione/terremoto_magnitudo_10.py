from __future__ import annotations

CARD_NAME = "Terremoto: Magnitudo 10"

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
                "owner": "any",
                "card_filter": {
                    "card_type_in": ["artefatto", "edificio"],
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
                "owner": "any",
                "card_filter": {
                    "card_type_in": ["artefatto", "edificio"],
                },
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {
                "action": "send_to_graveyard",
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "effect": {
                "action": "summon_card_from_hand",
                "placement_policy": "prompt_slot_required",
                "card_name": "Vulcano",
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "effect": {
                "action": "move_source_to_zone",
                "to_zone": "excommunicated",
            },
        },
    ],
}
