from __future__ import annotations

CARD_NAME = """Sacerdote Orologio"""

SCRIPT = {
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
            "effect": {"action": "destroy_linked_targets_from_source_tags", "flag": "orologio_link"},
        },
    ],
    "on_play_actions": [
        {
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
            },
            "effect": {"action": "add_link_tag_to_source_from_selected_target", "flag": "orologio_link"},
        },
    ],
}
