from __future__ import annotations

CARD_NAME = "Pietra Levigata"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "activate_once_per_turn": True,
    "play_targeting": "none",
    "activate_targeting": "guided",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_saint_defeated_or_destroyed",
            },
            "target": {
                "type": "source_card",
            },
            "effect": {
                "action": "destroy_source_if_linked_to_event_card",
            },
        },
    ],
    "on_play_actions": [],
    "on_activate_actions": [
        {
            "target": {
                "type": "selected_target",
                "owner": "opponent",
                "zone": "field",
                "card_filter": {
                    "card_type_in": ["santo", "token"],
                },
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {
                "action": "absorb_target_stats_and_link",
            },
        },
    ],
}
