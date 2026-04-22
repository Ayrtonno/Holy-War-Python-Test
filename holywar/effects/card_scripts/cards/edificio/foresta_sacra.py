from __future__ import annotations

CARD_NAME = """Foresta Sacra"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "grants_targeting_immunity_to_friendly_cards": [
        {
            "card_filter": {"name_contains": "Albero"},
            "source_card_types": ["benedizione", "maledizione"],
        }
    ],
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_card_excommunicated",
                "frequency": "each_turn",
                "condition": {"event_card_owner": "me"},
            },
            "target": {
                "type": "event_card",
                "card_filter": {"name_contains": "Albero", "card_type_in": ["santo", "token"]},
            },
            "effect": {"action": "move_to_relicario"},
        },
    ],
    "on_play_actions": [],
}

