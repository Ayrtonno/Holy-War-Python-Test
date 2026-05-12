from __future__ import annotations

CARD_NAME = "Muschio Tossico"

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
                "event": "on_this_card_destroyed",
                "frequency": "each_turn",
            },
            "target": {
                "type": "selected_target",
                "zone": "deck",
                "owner": "opponent",
                "min_targets": 1,
                "max_targets": 1,
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {
                "action": "send_to_graveyard",
            },
        }
    ],
    "on_play_actions": [],
}