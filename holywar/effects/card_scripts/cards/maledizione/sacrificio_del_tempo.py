from __future__ import annotations

CARD_NAME = 'Sacrificio del Tempo'

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "can_play_from_hand": False,
    "play_targeting": "none",
    "play_requirements": {
        "auto_activate_when_discarded_from_hand_by_effect": True,
    },
    "triggered_effects": [],
    "on_play_actions": [
        {
            "activation_mode": "mandatory_auto",
            "target": { "target_policy": "optional_resolve", "selection_mode": "prompt", "cancel_behavior": "abort_step","type": "source_card"},
            "effect": {
                "action": "discard_hand_then_pressure_opponent",
                "amount": 1,
                "target_player": "opponent",
                "choice_title": "Sacrificio del Tempo",
                "choice_prompt": "Seleziona i bersagli avversari da inviare al cimitero.",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
        },
    ],
}
