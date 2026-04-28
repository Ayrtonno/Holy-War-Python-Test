from __future__ import annotations

CARD_NAME = """Iside"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_enter_field", "frequency": "each_time"},
            "condition": {"event_card_name_is": "Iside"},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {"name_equals": "Osiride"},
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "trigger": {"event": "on_enter_field", "frequency": "each_time"},
            "condition": {"event_card_name_is": "Iside"},
            "target": {
                "type": "selected_target",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {"name_equals": "Osiride"},
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "summon_target_to_field"},
        },
    ],
    "on_play_actions": [],
}
