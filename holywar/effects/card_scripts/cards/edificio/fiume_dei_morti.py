from __future__ import annotations

CARD_NAME = """Fiume dei Morti"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_card_sent_to_graveyard",
                "frequency": "each_turn",
                "condition": {
                    "all_of": [
                        {"event_card_owner": "me"},
                        {"payload_from_zone_in": ["attack", "defense", "artifact", "building"]},
                    ]
                },
            },
            "target": {"type": "event_card"},
            "effect": {"action": "move_to_hand"},
        }
    ],
    "on_play_actions": [],
}
