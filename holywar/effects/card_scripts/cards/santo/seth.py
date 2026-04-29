from __future__ import annotations

CARD_NAME = """Seth"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_enter_field", "frequency": "each_time"},
            "condition": {"event_card_name_is": "Seth"},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "deck",
                "owner": "me",
                "card_filter": {"name_equals": "Osiride"},
            },
            "effect": {
                "action": "optional_recover_cards",
                "from_zone": "deck",
                "to_zone": "graveyard",
                "min_targets": 0,
                "max_targets": 1,
            },
        },
    ],
    "on_play_actions": [],
}
