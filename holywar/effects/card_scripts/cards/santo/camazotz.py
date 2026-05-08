from __future__ import annotations

CARD_NAME = """Camazotz"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_this_card_kills_in_battle",
                "frequency": "each_time",
            },
            "target": {"type": "source_card"},
            "effect": {"action": "remove_sin", "amount": 2, "target_player": "me"},
        },
        {
            "trigger": {
                "event": "on_this_card_kills_in_battle",
                "frequency": "each_time",
            },
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {"card_type_in": ["santo"], "strength_lte": 6},
            },
            "effect": {"action": "choose_targets_and_summon_to_field", "min_targets": 1, "max_targets": 1},
        },
    ],
    "on_play_actions": [],
}

