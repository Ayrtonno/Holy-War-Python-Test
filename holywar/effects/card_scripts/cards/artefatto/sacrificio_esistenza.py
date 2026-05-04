from __future__ import annotations

CARD_NAME = "Sacrificio: Esistenza"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_token_summoned", "frequency": "each_time"},
            "condition": {
                "all_of": [
                    {"event_card_name_is": "Token Gub-ner"},
                    {"event_card_owner": "me"},
                ]
            },
            "target": {"type": "event_card"},
            "effect": {"action": "destroy_card"},
        },
        {
            "trigger": {"event": "on_token_summoned", "frequency": "each_time"},
            "condition": {
                "all_of": [
                    {"event_card_name_is": "Token Gub-ner"},
                    {"event_card_owner": "me"},
                ]
            },
            "target": {"type": "source_card"},
            "effect": {"action": "excommunicate_top_cards_from_relicario", "target_player": "me", "amount": 1},
        },
        {
            "trigger": {"event": "on_token_summoned", "frequency": "each_time"},
            "condition": {
                "all_of": [
                    {"event_card_name_is": "Token Gub-ner"},
                    {"event_card_owner": "me"},
                ]
            },
            "target": {"type": "source_card"},
            "effect": {"action": "remove_sin", "target_player": "me", "amount": 3},
        },
    ],
    "on_play_actions": [],
}
