from __future__ import annotations

CARD_NAME = "Ph'kdam"

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
    "triggered_effects": [],
    "on_play_actions": [
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "selected_targets",
                "zone": "hand",
                "owner": "me",
                "card_filter": {
                    "exclude_event_card": True,
                },
                "min_targets": 6,
                "max_targets": 6,
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {
                "action": "send_to_graveyard",
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "selected_target",
                "zone": "relicario",
                "owner": "me",
                "card_filter": {
                    "card_type_in": ["artefatto"],
                },
                "min_targets": 1,
                "max_targets": 1,
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {
                "action": "summon_target_to_field",
                "placement_policy": "prompt_slot_required",
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "effect": {
                "action": "request_end_turn",
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "source_card",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {
                "action": "excommunicate_card",
            },
        },
    ],
}