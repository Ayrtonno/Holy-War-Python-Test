from __future__ import annotations

CARD_NAME = """Camazotz"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_saint_defeated_in_battle",
                "frequency": "each_turn",
                "condition": {
                    "event_card_owner": "opponent",
                },
            },
            "target": {"type": "source_card"},
            "effect": {"action": "remove_sin", "amount": 2, "target_player": "me"},
        },
        {
            "trigger": {
                "event": "on_saint_defeated_in_battle",
                "frequency": "each_turn",
                "condition": {
                    "event_card_owner": "opponent",
                },
            },
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {"card_type_in": ["santo"], "strength_lte": 6},
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "trigger": {
                "event": "on_saint_defeated_in_battle",
                "frequency": "each_turn",
                "condition": {
                    "event_card_owner": "opponent",
                },
            },
            "target": {
                "type": "selected_target",
            },
            "effect": {"action": "summon_target_to_field"},
        },
    ],
    "on_play_actions": [],
}

