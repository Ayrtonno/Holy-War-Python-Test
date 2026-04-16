from __future__ import annotations

CARD_NAME = """Paladino Corrotto"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_enter_field", "frequency": "each_turn"},
            "condition": {
                "all_of": [
                    {"event_card_name_is": "Paladino Corrotto"},
                    {"controller_has_saint_with_name": "Paladino della Fede"},
                ]
            },
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"name_contains": "Paladino della Fede"},
            },
            "effect": {"action": "excommunicate_card"},
        },
        {
            "trigger": {"event": "on_enter_field", "frequency": "each_turn"},
            "condition": {
                "all_of": [
                    {"event_card_name_is": "Paladino Corrotto"},
                    {"controller_has_saint_with_name": "Paladino della Fede"},
                ]
            },
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"name_contains": "Paladino Corrotto"},
            },
            "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"},
        }
    ],
    "on_play_actions": [],
}
