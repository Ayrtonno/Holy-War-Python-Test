from __future__ import annotations

CARD_NAME = """Custode dei Sigilli"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "seals_level_size": 6,
    "seals_faith_per_level": 3,
    "seals_strength_per_level": 3,
    "triggered_effects": [
        {
            "trigger": {"event": "on_enter_field", "frequency": "each_turn"},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"name_contains": "__no_target__"},
            },
            "effect": {"action": "add_seal_counter", "amount": 2},
        }
    ],
    "on_play_actions": [],
}
