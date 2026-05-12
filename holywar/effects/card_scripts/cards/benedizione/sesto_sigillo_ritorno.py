from __future__ import annotations

CARD_NAME = "Sesto Sigillo: Ritorno"

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
            "condition": {"controller_altare_sigilli_gte": 6},
            "target": {
                "type": "selected_target",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {
                    "card_type_in": ["santo", "benedizione", "maledizione", "artefatto", "edificio"],
                    "exclude_event_card": True,
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
            "condition": {"not": {"controller_altare_sigilli_gte": 6}},
            "target": {
                "type": "selected_target",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {
                    "card_type_in": ["santo"],
                    "exclude_event_card": True,
                },
                "min_targets": 1,
                "max_targets": 1,
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "move_to_hand"},
        },
    ],
}
