from __future__ import annotations

CARD_NAME = """Nefti"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_this_card_destroyed", "frequency": "each_time"},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {"name_equals": "Set"},
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "trigger": {"event": "on_this_card_destroyed", "frequency": "each_time"},
            "target": {
                "type": "selected_target",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {"name_equals": "Set"},
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "summon_target_to_field"},
        },
    ],
    "on_play_actions": [],
}
