from __future__ import annotations

CARD_NAME = "Li Tieguai"

TRIGGER_BAXIAN_DESTROYED = {
    "all_of": [
        {"event_card_owner": "me"},
        {"event_card_type_in": ["santo", "token"]},
        {"event_card_name_contains": "ba xian"},
        {"payload_from_zone_in": ["attack", "defense", "field"]},
        {"not": {"event_card_name_is": "Li Tieguai"}},
    ]
}

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_card_sent_to_graveyard",
                "frequency": "each_time",
                "condition": TRIGGER_BAXIAN_DESTROYED,
            },
            "target": {"type": "source_card"},
            "effect": {"action": "decrease_strength", "amount": 2},
        },
        {
            "trigger": {
                "event": "on_card_sent_to_graveyard",
                "frequency": "each_time",
                "condition": TRIGGER_BAXIAN_DESTROYED,
            },
            "target": {"type": "event_card"},
            "effect": {"action": "summon_target_to_field"},
        },
        {
            "trigger": {
                "event": "on_card_sent_to_graveyard",
                "frequency": "each_time",
                "condition": TRIGGER_BAXIAN_DESTROYED,
            },
            "target": {"type": "source_card"},
            "effect": {"action": "destroy_source_if_effective_strength_lte", "threshold": 0},
        },
    ],
    "on_play_actions": [],
}
