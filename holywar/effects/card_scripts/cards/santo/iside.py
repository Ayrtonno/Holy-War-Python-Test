from __future__ import annotations

CARD_NAME = """Iside"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "scripted",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "on_enter_actions": [
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {"name_equals": "Osiride"},
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "target": {
                "type": "selected_target",
            },
            "effect": {"action": "summon_target_to_field"},
        },
    ],
    "on_play_actions": [],
}
