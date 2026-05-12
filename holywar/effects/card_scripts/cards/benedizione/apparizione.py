from __future__ import annotations

CARD_NAME = "Apparizione"

ELEMENT_ARTIFACTS = ["Terra", "Aria", "Fuoco", "Acqua"]

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
    "play_requirements": {
        "all_of": [
            {
                "controller_has_cards": {
                    "owner": "me",
                    "zone": "field",
                    "card_filter": {"name_equals": name},
                }
            }
            for name in ELEMENT_ARTIFACTS
        ]
    },
    "triggered_effects": [],
    "on_play_actions": [
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "selected_target",
                "owner": "me",
                "zone": "relicario",
                "zones": ["relicario", "graveyard"],
                "card_filter": {
                    "name_equals": "Dio, il Creatore",
                    "card_type_in": ["santo"],
                },
                "min_targets": 1,
                "max_targets": 1,
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "move_to_hand"},
        },
        {
            "activation_mode": "mandatory_auto",
            "target": { "target_policy": "optional_resolve", "selection_mode": "prompt", "cancel_behavior": "abort_step","type": "source_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "shuffle_deck", "target_player": "me"},
        },
    ],
}
