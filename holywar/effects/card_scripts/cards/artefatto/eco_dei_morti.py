from __future__ import annotations

CARD_NAME = "Eco dei Morti"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_card_sent_to_graveyard",
                "frequency": "each_time",
                "condition": {
                    "event_card_owner": "me",
                    "event_card_type_in": ["santo"],
                    "payload_from_zone_in": ["attack"],
                },
            },
            "target": {"type": "source_card"},
            "effect": {
                "action": "summon_generated_token",
                "card_name": "Spirito Vacuo",
                "owner": "me",
                "zone": "attack",
            },
        },
        {
            "trigger": {
                "event": "on_card_sent_to_graveyard",
                "frequency": "each_time",
                "condition": {
                    "event_card_owner": "me",
                    "event_card_type_in": ["santo"],
                    "payload_from_zone_in": ["defense"],
                },
            },
            "target": {"type": "source_card"},
            "effect": {
                "action": "summon_generated_token",
                "card_name": "Spirito Vacuo",
                "owner": "me",
                "zone": "defense",
            },
        },
    ],
    "on_play_actions": [],
}
