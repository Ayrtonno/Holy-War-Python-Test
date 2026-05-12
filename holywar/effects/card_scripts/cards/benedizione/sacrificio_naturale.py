from __future__ import annotations

CARD_NAME = 'Sacrificio Naturale'

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
    "play_requirements": {
        "not": {
            "controller_has_cards": {
                "owner": "opponent",
                "zone": "defense",
                "min_count": 1,
                "card_filter": {"card_type_in": ["santo", "token"]},
            }
        }
    },
    "on_play_actions": [
        {
            "activation_mode": "mandatory_auto",
            "target": { "target_policy": "optional_resolve", "selection_mode": "prompt", "cancel_behavior": "abort_step","type": "source_card"},
            "effect": {
                "action": "summon_generated_token",
                "placement_policy": "prompt_slot_required",
                "card_name": "Token Sacrificale",
                "amount": 3,
                "owner": "opponent",
                "zone": "defense",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
        }
    ],
}
