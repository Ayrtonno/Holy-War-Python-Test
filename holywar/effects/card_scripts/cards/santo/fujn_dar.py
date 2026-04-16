from __future__ import annotations

CARD_NAME = """Fujn-dar"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_this_card_kills_in_battle", "frequency": "each_turn"},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "opponent",
                "card_filter": {"name_contains": "__no_target__"},
            },
            "effect": {"action": "mill_cards", "amount": 2, "target_player": "opponent"},
        }
    ],
    "on_play_actions": [],
}
