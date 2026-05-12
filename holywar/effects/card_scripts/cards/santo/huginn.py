from __future__ import annotations

CARD_NAME = """Huginn"""

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "noop",
    "play_targeting": "none",
    "on_enter_mode": "scripted",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "on_play_actions": [],
    "on_enter_actions": [
        {
            "activation_mode": "mandatory_auto",
            "condition": {"controller_has_saint_with_name": "Odino"},
            "effect": {"action": "optional_draw_from_top_n_then_shuffle", "amount": 3, "target_player": "me"},
        },
    ],
}
