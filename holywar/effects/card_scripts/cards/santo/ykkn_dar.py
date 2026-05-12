from __future__ import annotations

CARD_NAME = "Ykknødar"

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "can_play_from_hand": False,
    "protection_rules": [
        {
            "event": "destroy_by_effect",
            "source_owner": "any",
            "target_owner": "friendly",
            "target_card_types": ["santo", "token"],
            "target_name_contains": "Ykknødar",
        }
    ],
    "triggered_effects": [
        {
            "trigger": {"event": "on_enter_field", "frequency": "each_time"},
            "condition": {"event_card_name_is": "Ykknødar"},
            "target": {"type": "source_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "prevent_specific_card_from_attacking", "amount": 1},
        },
        {
            "trigger": {"event": "on_my_turn_start", "frequency": "each_turn"},
            "target": {"type": "source_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "prevent_specific_card_from_attacking", "amount": 1},
        },
        {
            "trigger": {
                "event": "on_card_drawn",
                "frequency": "each_time",
                "condition": {"event_card_owner": "opponent"},
            },
            "target": {"type": "source_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "remove_sin", "amount": 3, "target_player": "me"},
        },
    ],
    "on_play_actions": [],
}

