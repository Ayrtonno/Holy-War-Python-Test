from __future__ import annotations

CARD_NAME = """Sacerdote Orologio"""

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_saint_defeated_in_battle",
                "frequency": "each_time",
                "condition": {"event_card_name_is": "Sacerdote Orologio"},
            },
            "target": {"type": "source_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "destroy_linked_targets_from_source_tags", "flag": "orologio_link"},
        },
    ],
    "on_play_actions": [
        {
            "activation_mode": "mandatory_auto",
            "condition": {"target_is_damaged": True},
            "target": {
                "type": "selected_target",
                "zone": "field",
                "owner": "opponent",
                "card_filter": {
                    "card_type_in": ["santo", "token"],
                    "crosses_lte": 5,
                },
                "min_targets": 1,
                "max_targets": 1,
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "add_link_tag_to_source_from_selected_target", "flag": "orologio_link"},
        },
    ],
}
