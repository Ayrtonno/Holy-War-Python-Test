from __future__ import annotations

CARD_NAME = """Loki"""

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "play_targeting": "none",
    "activate_targeting": "guided",
    "triggered_effects": [],
    "on_play_actions": [],
    "on_activate_actions": [
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "source_card",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "remove_from_board_no_sin"},
        },
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "selected_target",
                "owner": "me",
                "zones": ["hand"],
                "card_filter": {
                    "card_type_in": ["santo"],
                    "name_in": ["Fenrir", "Jormungandr"],
                },
                "min_targets": 1,
                "max_targets": 1,
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "summon_card_from_hand", "placement_policy": "prompt_slot_required"},
        },
    ],
}

