from __future__ import annotations

CARD_NAME = """Acqua"""
ELEMENT_ARTIFACTS = ["Aria", "Fuoco", "Terra", "Acqua"]
CREATOR_NAME = "Dio, il Creatore"

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "activate_targeting": "guided",
    "protection_rules": [
        {
            "event": "target_by_effect",
            "source_owner": "enemy",
            "target_owner": "friendly",
            "source_card_types": ["maledizione"],
            "target_card_types": ["santo", "token"],
        }
    ],
    "triggered_effects": [],
    "on_play_actions": [],
    "on_activate_actions": [
        {
            "activation_mode": "mandatory_auto",
            "condition": {
                "all_of": [
                    *[
                        {
                            "controller_has_cards": {
                                "owner": "me",
                                "zone": "field",
                                "card_filter": {"name_equals": name},
                            }
                        }
                        for name in ELEMENT_ARTIFACTS
                    ],
                    {
                        "controller_has_cards": {
                            "owner": "me",
                            "zones": ["hand", "deck"],
                            "card_filter": {"name_equals": CREATOR_NAME, "card_type_in": ["santo"]},
                            "min_count": 1,
                        }
                    },
                ]
            },
            "target": {
                "type": "selected_target",
                "owner": "me",
                "zone": "deck",
                "zones": ["hand", "deck"],
                "card_filter": {"name_equals": CREATOR_NAME, "card_type_in": ["santo"]},
                "min_targets": 1,
                "max_targets": 1,
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "summon_named_card"},
                "placement_policy": "prompt_slot_required",
            "placement_policy": "prompt_slot_required",
        }
    ],
}
