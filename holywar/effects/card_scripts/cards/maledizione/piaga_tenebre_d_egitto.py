from __future__ import annotations

CARD_NAME = "Piaga: Tenebre d'Egitto"

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "guided",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "source_card",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "set_next_turn_draw_override", "amount": 2, "target_player": "opponent"},
        },
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "selected_target",
                "zone": "deck",
                "owner": "me",
                "card_filter": {"name_contains": "Piaga"},
                "min_targets": 0,
                "max_targets": 1,
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "move_to_hand"},
        },
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "source_card",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "shuffle_deck", "target_player": "me"},
        },
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "source_card",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "inflict_sin", "amount": 1, "target_player": "me"},
        },
    ],
}
