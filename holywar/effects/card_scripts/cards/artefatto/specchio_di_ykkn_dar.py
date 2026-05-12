from __future__ import annotations

CARD_NAME = "Specchio di Ykknødar"

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "play_requirements": {
        "all_of": [
            {"my_sin_gte": 51},
            {"opponent_sin_gte": 51},
        ]
    },
    "triggered_effects": [],
    "on_play_actions": [
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "cards_controlled_by_owner",
                "owner": "any",
                "zones": ["field", "hand", "graveyard"],
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "excommunicate_card_no_sin"},
        },
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "cards_controlled_by_owner",
                "owner": "me",
                "zones": ["hand", "relicario", "excommunicated"],
                "card_filter": {"name_equals": "Ykknødar"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "selected_target",
                "owner": "me",
                "zones": ["hand", "relicario", "excommunicated"],
                "card_filter": {"name_equals": "Ykknødar"},
                "min_targets": 1,
                "max_targets": 1,
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "summon_named_card", "placement_policy": "prompt_slot_required"},
                "placement_policy": "prompt_slot_required",
            "placement_policy": "prompt_slot_required",
        },
        { "activation_mode": "mandatory_auto","effect": {"action": "move_source_to_zone", "to_zone": "excommunicated"}},
    ],
}
