from __future__ import annotations

CARD_NAME = """Moribondo"""

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "own_saint",
    "play_requirements": {
        "allow_quick_play_out_of_turn": True,
        "quick_play_excommunicate_self": True,
        "quick_play_grant_blessed_tag": "moribondo_shield",
    },
    "triggered_effects": [
    ],
    "on_play_actions": [],
}

