from __future__ import annotations

CARD_NAME = """Pianta Carnivora"""

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "strength_bonus_rules": [
        {
            "if_card_name": "Pianta Carnivora",
            "controller_has_card_with_name": "Insetto della Palude",
            "controller_has_card_zone": "field",
            "self_bonus": 2,
        }
    ],
    "faith_bonus_rules": [
        {
            "if_card_name": "Pianta Carnivora",
            "controller_has_card_with_name": "Insetto della Palude",
            "controller_has_card_zone": "field",
            "self_bonus": 2,
        }
    ],
    "triggered_effects": [
    ],
    "on_play_actions": [],
}