from __future__ import annotations

CARD_NAME = """Altare dei Sette Sigilli"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "is_altare_sigilli": True,
    "altare_seal_shield_from_source_crosses": True,
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_saint_defeated_or_destroyed",
                "frequency": "each_turn",
                "condition": {"event_card_owner": "me"},
            },
            "target": {"type": "source_card"},
            "effect": {"action": "add_seal_counter", "amount": 1},
        },
        {
            "trigger": {
                "event": "on_card_played",
                "frequency": "each_turn",
                "condition": {
                    "all_of": [
                        {"event_card_owner": "me"},
                        {"event_card_name_contains": "Sigillo"},
                    ]
                },
            },
            "target": {"type": "source_card"},
            "effect": {"action": "add_seal_counter", "amount": 1},
        },
        {
            "trigger": {"event": "on_this_card_leaves_field", "frequency": "each_time"},
            "target": {"type": "source_card"},
            "effect": {"action": "remove_seal_counter", "amount": 999},
        },
    ],
    "on_play_actions": [],
}

