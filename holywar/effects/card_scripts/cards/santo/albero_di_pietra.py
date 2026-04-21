from __future__ import annotations

CARD_NAME = "Albero di Pietra"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_this_card_destroyed",
                "condition": {
                    "payload_reason_in": ["battle"],
                },
            },
            "target": {
                "type": "source_card",
            },
            "effect": {
                "action": "optional_recover_matching_then_shuffle",
                "target_player": "me",
                "from_zone": "graveyard",
                "to_zone": "relicario",
                "card_name": "Pietra",
                "shuffle_after": True,
                "to_zone_if": "excommunicated",
            },
        },
    ],
    "on_play_actions": [],
}
