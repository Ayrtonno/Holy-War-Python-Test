from __future__ import annotations

CARD_NAME = "Ph'kdam"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "guided",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "selected_targets",
                "zone": "hand",
                "owner": "me",
                "card_filter": {
                    "exclude_event_card": True,
                },
                "min_targets": 6,
                "max_targets": 6,
            },
            "effect": {
                "action": "send_to_graveyard",
            },
        },
        {
            "target": {
                "type": "selected_target",
                "zone": "relicario",
                "owner": "me",
                "card_filter": {
                    "card_type_in": ["artefatto"],
                },
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {
                "action": "summon_target_to_field",
            },
        },
        {
            "effect": {
                "action": "request_end_turn",
            },
        },
        {
            "target": {
                "type": "source_card",
            },
            "effect": {
                "action": "excommunicate_card",
            },
        },
    ],
}