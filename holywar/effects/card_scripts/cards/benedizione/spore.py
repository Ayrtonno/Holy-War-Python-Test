from __future__ import annotations

CARD_NAME = "Spore"

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
    "on_play_actions": [
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "cards_controlled_by_owner",
                "owner": "me",
                "zone": "hand",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {
                "action": "move_to_relicario",
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "effect": {
                "action": "shuffle_deck",
                "target_player": "me",
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "effect": {
                "action": "set_next_turn_draw_override",
                "amount": 8,
                "target_player": "me",
            },
        },
    ],
}
