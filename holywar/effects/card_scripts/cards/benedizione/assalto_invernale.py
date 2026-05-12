from __future__ import annotations

CARD_NAME = "Assalto Invernale"

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
        "controller_saints_sent_to_graveyard_this_turn_gte": 3,
    },
    "triggered_effects": [],
    "on_play_actions": [
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "selected_target",
                "owner": "me",
                "zone": "graveyard",
                "zones": ["graveyard", "deck"],
                "card_filter": {
                    "name_in": ["Fenrir", "Jormungandr"],
                },
                "min_targets": 1,
                "max_targets": 1,
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {
                "action": "summon_named_card",
                "placement_policy": "prompt_slot_required",
            },
        },
    ],
}
