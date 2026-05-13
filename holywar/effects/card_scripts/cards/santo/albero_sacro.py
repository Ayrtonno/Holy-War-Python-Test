from __future__ import annotations

CARD_NAME = """Albero Sacro"""

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "noop",
    "on_enter_mode": "scripted",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "auto_play_on_draw": True,
    "end_turn_on_draw": True,
    "triggered_effects": [
        {
            "trigger": {"event": "on_preparation_complete", "frequency": "each_turn"},
            "target": {
                "type": "empty_saint_slots_controlled_by_owner",
                "owner": "me",
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "trigger": {"event": "on_preparation_complete", "frequency": "each_turn"},
            "target": {"type": "source_card"},
            "effect": {
                "action": "summon_generated_token",
                "card_name": "Token Albero",
                "owner": "me",
                "position": "selected_target_slot",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
        },
        {
            "trigger": {"event": "on_my_turn_end", "frequency": "each_turn"},
            "target": {
                "type": "empty_saint_slots_controlled_by_owner",
                "owner": "me",
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "trigger": {"event": "on_opponent_turn_end", "frequency": "each_turn"},
            "target": {
                "type": "empty_saint_slots_controlled_by_owner",
                "owner": "me",
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "trigger": {"event": "on_my_turn_end", "frequency": "each_turn"},
            "target": {"type": "source_card"},
            "effect": {
                "action": "summon_generated_token",
                "card_name": "Token Albero",
                "owner": "me",
                "position": "selected_target_slot",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
        },
        {
            "trigger": {"event": "on_opponent_turn_end", "frequency": "each_turn"},
            "target": {"type": "source_card"},
            "effect": {
                "action": "summon_generated_token",
                "card_name": "Token Albero",
                "owner": "me",
                "position": "selected_target_slot",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
        },
        {
            "trigger": {"event": "on_saint_defeated_in_battle", "frequency": "each_turn"},
            "condition": {"event_card_name_is": "Token Albero"},
            "target": {
                "type": "source_card",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "increase_faith", "amount": 2},
        },
    ],
    "on_play_actions": [],
    "on_enter_actions": [
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "empty_saint_slots_controlled_by_owner",
                "owner": "me",
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
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
                "action": "summon_generated_token",
                "placement_policy": "prompt_slot_required",
                "card_name": "Token Albero",
                "owner": "me",
                "position": "selected_target_slot",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
        },
    ],
}
