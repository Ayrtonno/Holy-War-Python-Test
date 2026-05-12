from __future__ import annotations

CARD_NAME = "Elementi della Creazione"

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
        "controller_free_artifact_slots_gte": 2,
    },
    "triggered_effects": [],
    "on_play_actions": [
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "selected_targets",
                "owner": "me",
                "zone": "relicario",
                "zones": ["relicario", "graveyard"],
                "card_filter": {
                    "card_type_in": ["artefatto"],
                    "name_in": ELEMENT_ARTIFACTS,
                },
                "min_targets": 2,
                "max_targets": 2,
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "summon_target_to_field", "placement_policy": "prompt_slot_required"},
                "placement_policy": "prompt_slot_required",
            "placement_policy": "prompt_slot_required",
        },
        {
            "activation_mode": "mandatory_auto",
            "target": { "target_policy": "optional_resolve", "selection_mode": "prompt", "cancel_behavior": "abort_step","type": "source_card"},
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "shuffle_deck", "target_player": "me"},
        },
    ],
}
