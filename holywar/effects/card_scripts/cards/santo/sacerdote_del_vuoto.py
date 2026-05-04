from __future__ import annotations

CARD_NAME = """Sacerdote del Vuoto"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "scripted",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_card_excommunicated", "frequency": "each_time"},
            "target": {"type": "source_card"},
            "effect": {"action": "increase_strength", "amount": 1},
        },
    ],
    "on_play_actions": [],
    "on_enter_actions": [
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "excommunicated",
                "owner": "me",
            },
            "effect": {"action": "choose_targets", "min_targets": 0, "max_targets": 1},
        },
        {
            "target": {
                "type": "selected_target",
                "zone": "excommunicated",
                "owner": "me",
                "min_targets": 0,
                "max_targets": 1,
            },
            "effect": {"action": "move_to_relicario"},
        },
        {
            "target": {
                "type": "selected_target",
                "zone": "deck",
                "owner": "me",
                "min_targets": 0,
                "max_targets": 1,
            },
            "effect": {"action": "shuffle_target_owner_decks"},
        },
    ],
}
