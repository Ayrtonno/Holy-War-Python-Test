from __future__ import annotations

CARD_NAME = """Atum"""

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_cost_fixed": 0,
    "halves_friendly_saint_play_cost": True,
    "halve_friendly_saint_play_cost_excludes_self": True,
    "triggered_effects": [],
    "on_play_actions": [],
}
