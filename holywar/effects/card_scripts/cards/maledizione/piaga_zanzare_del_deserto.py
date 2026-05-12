from __future__ import annotations

CARD_NAME = "Piaga: Zanzare del Deserto"

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "opponent",
                "card_filter": {"card_type_in": ["santo", "token"]},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "decrease_faith", "amount": 3},
        },
        {
            "activation_mode": "mandatory_auto",
            "target": { "target_policy": "optional_resolve", "selection_mode": "prompt", "cancel_behavior": "abort_step","type": "source_card"},
            "effect": {
                "action": "optional_recover_matching_then_shuffle",
                "from_zone": "graveyard",
                "to_zone": "hand",
                "card_name": "Piaga",
                "amount": 1,
                "shuffle_after": False,
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "target": { "target_policy": "optional_resolve", "selection_mode": "prompt", "cancel_behavior": "abort_step","type": "source_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "inflict_sin", "amount": 1, "target_player": "me"},
        },
    ],
}
