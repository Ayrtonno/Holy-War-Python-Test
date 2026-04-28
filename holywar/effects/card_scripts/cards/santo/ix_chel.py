from __future__ import annotations

CARD_NAME = """Ix Chel"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_enter_field",
                "frequency": "each_time",
                "condition": {
                    "all_of": [
                        {"event_card_name_is": "Ix Chel"},
                        {"payload_from_zone_in": ["hand", "deck", "relicario"]},
                    ]
                },
            },
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "deck",
                "owner": "opponent",
                "card_filter": {"top_n_from_zone": 1},
            },
            "effect": {"action": "send_to_graveyard"},
        },
        {
            "trigger": {
                "event": "on_enter_field",
                "frequency": "each_time",
                "condition": {
                    "all_of": [
                        {"event_card_name_is": "Ix Chel"},
                        {"payload_from_zone_in": ["graveyard"]},
                    ]
                },
            },
            "target": {"type": "source_card"},
            "effect": {"action": "increase_strength", "amount": 4},
        },
    ],
    "on_play_actions": [],
}
