from __future__ import annotations

CARD_NAME = "Missionario"

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "auto",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_owner": "opponent",
    "attack_targeting": "untargetable",
    "play_targeting": "none",
    "triggered_effects": [
        {
            "trigger": {"event": "on_turn_end", "frequency": "each_turn"},
            "target": {"type": "source_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "decrease_faith", "amount": 3},
        },
        {
            "trigger": {"event": "on_saint_destroyed_by_effect", "frequency": "each_turn"},
            "condition": {
                "all_of": [
                    {"event_card_name_is": "Missionario"},
                    {"payload_reason_in": ["effect"]},
                ]
            },
            "target": {"type": "source_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "inflict_sin", "amount": 6, "target_player": "opponent"},
        },
        {
            "trigger": {"event": "on_saint_destroyed_by_effect", "frequency": "each_turn"},
            "condition": {
                "all_of": [
                    {"event_card_name_is": "Missionario"},
                    {"payload_reason_in": ["effect"]},
                ]
            },
            "target": {"type": "event_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "move_to_deck_bottom"},
        },
        {
            "trigger": {"event": "on_saint_destroyed_by_effect", "frequency": "each_turn"},
            "condition": {
                "all_of": [
                    {"event_card_name_is": "Missionario"},
                    {"payload_reason_in": ["effect"]},
                ]
            },
            "target": {"type": "event_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "shuffle_deck"},
        },
    ],
    "on_play_actions": [],
}