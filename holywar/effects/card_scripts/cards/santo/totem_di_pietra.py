from __future__ import annotations

CARD_NAME = "Totem di Pietra"

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "can_attack": False,
    "play_requirements": {
        "consume_all_remaining_inspiration": True,
        "set_source_faith_from_paid_inspiration_multiplier": 3,
        "store_paid_inspiration_on_source": True,
    },
    "triggered_effects": [],
    "on_play_actions": [],
}
