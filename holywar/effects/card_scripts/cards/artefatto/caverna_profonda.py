from __future__ import annotations

CARD_NAME = """Caverna Profonda"""

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
                    "payload_from_zone_in": ["attack", "defense", "artifact", "building", "field"],
                },
            },
            "target": {
                "type": "event_card",
                "card_filter": {"name_contains": "Pietra"},
            },
            "effect": {"action": "move_to_relicario"},
        }
    ],
    "on_play_actions": [],
}
