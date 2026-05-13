from __future__ import annotations

CARD_NAME = "Lu Dongbin"

HAS_OTHER_BAXIAN = {
    "controller_has_cards": {
        "zones": ["field"],
        "owner": "me",
        "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
        # On-play resolves after Lu Dongbin enters the field, so min_count=2
        # means "Lu Dongbin + at least one other Ba Xian".
        "min_count": 2,
    }
}

HAS_OPP_ARTIFACT = {
    "controller_has_cards": {
        "zones": ["field"],
        "owner": "opponent",
        "card_filter": {"card_type_in": ["artefatto"]},
        "min_count": 1,
    }
}

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "auto",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "activation_mode": "mandatory_auto",
            "condition": {"all_of": [HAS_OTHER_BAXIAN, HAS_OPP_ARTIFACT]},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "opponent",
                "card_filter": {"card_type_in": ["artefatto"]},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {
                "all_of": [
                    HAS_OTHER_BAXIAN,
                    HAS_OPP_ARTIFACT,
                    {"selected_target_exists": True},
                ]
            },
            "target": {
                "type": "selected_target",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "destroy_card"},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {"not": HAS_OTHER_BAXIAN},
            "target": {
                "type": "source_card",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "increase_strength", "amount": 2},
        },
    ],
}
