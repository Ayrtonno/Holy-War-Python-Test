from __future__ import annotations

CARD_NAME = """Albero Sacro"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "auto_play_on_draw": True,
    "end_turn_on_draw": True,
    "triggered_effects": [
        {
            "trigger": {"event": "on_my_turn_end", "frequency": "each_turn"},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "deck",
                "owner": "me",
                "card_filter": {"name_contains": "Token Albero"},
                "max_targets": 1,
            },
            "effect": {"action": "summon_named_card", "card_name": "Token Albero"},
        },
        {
            "trigger": {"event": "on_opponent_turn_end", "frequency": "each_turn"},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "deck",
                "owner": "me",
                "card_filter": {"name_contains": "Token Albero"},
                "max_targets": 1,
            },
            "effect": {"action": "summon_named_card", "card_name": "Token Albero"},
        },
        {
            "trigger": {"event": "on_saint_defeated_in_battle", "frequency": "each_turn"},
            "condition": {"event_card_name_is": "Token Albero"},
            "target": {"type": "source_card"},
            "effect": {"action": "increase_faith", "amount": 2},
        },
    ],
    "on_play_actions": [],
}
