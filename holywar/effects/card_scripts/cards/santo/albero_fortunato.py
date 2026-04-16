from __future__ import annotations

CARD_NAME = """Albero Fortunato"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_this_card_destroyed", "frequency": "each_turn"},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"name_contains": "__no_target__"},
            },
            "effect": {"action": "draw_cards", "amount": 2, "target_player": "me"},
        }
    ],
    "on_play_actions": [],
}

