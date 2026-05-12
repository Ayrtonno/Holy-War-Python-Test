from __future__ import annotations

CARD_NAME = """Segno Del Passato"""

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "modifies_enemy_saints_strength": -4,
    "triggered_effects": [],
    "on_play_actions": [],
}
