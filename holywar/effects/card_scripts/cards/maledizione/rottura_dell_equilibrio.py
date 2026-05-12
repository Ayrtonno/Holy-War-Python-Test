from __future__ import annotations

CARD_NAME = "Rottura dell'Equilibrio"

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
        {"effect": {"action": "inflict_sin", "amount": 3, "target_player": "opponent"}},
        {"effect": {"action": "inflict_sin", "amount": 1, "target_player": "me"}},
    ],
}
