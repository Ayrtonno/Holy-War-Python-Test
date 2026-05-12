from __future__ import annotations

CARD_NAME = "Protezione dall'Oscurità"

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "guided",
    "protection_rules": [
        {
            "event": "destroy_by_effect",
            "source_owner": "any",
            "target_owner": "friendly",
            "target_card_types": ["edificio"],
            "requires_source_to_be_equipped": True,
            "set_target_faith": "base",
            "excommunicate_source": True,
        }
    ],
    "triggered_effects": [],
    "on_play_actions": [
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "selected_target",
                "owner": "me",
                "zone": "building",
                "card_filter": {"card_type_in": ["edificio"]},
                "min_targets": 1,
                "max_targets": 1,
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "equip_card"},
        },
    ],
}
