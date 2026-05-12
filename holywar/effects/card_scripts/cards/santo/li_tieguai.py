from __future__ import annotations

CARD_NAME = "Li Tieguai"

TRIGGER_BAXIAN_DESTROYED = {
    "all_of": [
        {"source_on_field": True},
        {"event_card_owner": "me"},
        {"event_card_type_in": ["santo", "token"]},
        {"event_card_name_contains": "ba xian"},
        {"payload_from_zone_in": ["attack", "defense", "field"]},
        {"not": {"event_card_name_is": "Li Tieguai"}},
    ]
}

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "auto",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_card_sent_to_graveyard",
                "frequency": "each_time",
                "condition": TRIGGER_BAXIAN_DESTROYED,
            },
            "target": {"type": "source_card"},
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "decrease_strength", "amount": 2},
        },
        {
            "trigger": {
                "event": "on_card_sent_to_graveyard",
                "frequency": "each_time",
                "condition": TRIGGER_BAXIAN_DESTROYED,
            },
            "target": {"type": "event_card"},
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "summon_target_to_field"},
                "placement_policy": "prompt_slot_required",
        },
        {
            "trigger": {
                "event": "on_card_sent_to_graveyard",
                "frequency": "each_time",
                "condition": TRIGGER_BAXIAN_DESTROYED,
            },
            "target": {"type": "source_card"},
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "destroy_source_if_effective_strength_lte", "threshold": 0},
        },
    ],
    "on_play_actions": [],
}
