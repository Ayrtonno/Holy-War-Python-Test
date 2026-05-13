from __future__ import annotations

CARD_NAME = """Ciclicità Climatica"""

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "activate_once_per_turn": True,
    "activate_targeting": "guided",
    "triggered_effects": [],
    "on_play_actions": [],
    "on_activate_actions": [
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "selected_target",
                "owner": "me",
                "zone": "graveyard",
                "card_filter": {"card_type_in": ["santo", "token"], "crosses_lte": 4},
                "min_targets": 1,
                "max_targets": 1,
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "summon_target_to_field", "placement_policy": "prompt_slot_required"},
        }
    ],
}
