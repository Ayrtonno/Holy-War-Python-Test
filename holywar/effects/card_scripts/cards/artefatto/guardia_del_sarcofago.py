from __future__ import annotations

CARD_NAME = "Guardia del Sarcofago"

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_attack_declared",
                "frequency": "each_turn",
                "exclusive_trigger_per_turn": True,
                "condition": {
                    "all_of": [
                        {"event_card_owner": "opponent"},
                        {"payload_target_slot_is_set": False},
                    ]
                },
            },
            "target": {"type": "source_card"},
            "effect": {
                "action": "set_attack_shield_this_turn",
                "target_player": "me",
                "usage_limit_per_turn": 1,
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
        },
        {
            "trigger": {
                "event": "on_attack_declared",
                "frequency": "each_turn",
                "exclusive_trigger_per_turn": True,
                "condition": {
                    "all_of": [
                        {"event_card_owner": "opponent"},
                        {"payload_target_slot_is_set": False},
                    ]
                },
            },
            "target": {"type": "source_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "decrease_faith", "amount": 2, "usage_limit_per_turn": 1},
        },
        {
            "trigger": {
                "event": "on_attack_declared",
                "frequency": "each_turn",
                "exclusive_trigger_per_turn": True,
                "condition": {
                    "all_of": [
                        {"event_card_owner": "opponent"},
                        {"payload_target_slot_is_set": False},
                        {"target_current_faith_lte": 0},
                    ]
                },
            },
            "target": {"type": "source_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "send_to_graveyard", "usage_limit_per_turn": 1},
        },
    ],
    "on_play_actions": [],
}
