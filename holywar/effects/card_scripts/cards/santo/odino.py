from __future__ import annotations

CARD_NAME = """Odino"""

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "strength_bonus_rules": [
        {"artifact_name": "Gungnir", "self_bonus": 4},
    ],
    "strength_gain_on_damage_to_enemy_saint": 1,
    "strength_gain_on_lethal_to_enemy_saint": 2,
    "triggered_effects": [],
    "on_play_actions": [],
}

