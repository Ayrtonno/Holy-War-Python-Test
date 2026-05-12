from __future__ import annotations

CARD_NAME = "Zhuangzi, Sognatore delle Farfalle"

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        { "activation_mode": "mandatory_auto","effect": {"action": "draw_cards", "amount": 1, "target_player": "me"}},
        { "activation_mode": "mandatory_auto","effect": {"action": "draw_cards", "amount": 1, "target_player": "opponent"}},
        {
            "activation_mode": "mandatory_auto",
            "condition": {"controller_hand_size_equals_opponent": True},
            "target": { "target_policy": "optional_resolve", "selection_mode": "prompt", "cancel_behavior": "abort_step","type": "source_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "increase_strength", "amount": 2},
        },
    ],
}
