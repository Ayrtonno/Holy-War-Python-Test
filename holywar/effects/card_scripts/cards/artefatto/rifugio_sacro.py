from __future__ import annotations

CARD_NAME = "Rifugio Sacro"

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "prevent_incoming_damage_if_less_than": 3,
    "prevent_incoming_damage_to_card_types": ["santo", "token"],
    "triggered_effects": [],
    "on_play_actions": [],
}
