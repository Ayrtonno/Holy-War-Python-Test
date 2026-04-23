from __future__ import annotations

CARD_NAME = """Profanatore"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "scripted",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_saint_defeated_or_destroyed",
                "frequency": "each_turn",
                "condition": {
                    "all_of": [
                        {"event_card_name_is": "Profanatore"},
                        {"event_card_owner": "me"},
                    ]
                },
            },
            "target": {"type": "event_card"},
            "effect": {"action": "excommunicate_card_no_sin"},
        },
    ],
    "on_play_actions": [
        {"effect": {"action": "draw_cards", "amount": 0, "target_player": "me"}},
    ],
    "on_enter_actions": [
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {"card_type_in": ["artefatto"]},
            },
            "effect": {"action": "choose_targets", "min_targets": 0, "max_targets": 1},
        },
        {
            "target": {
                "type": "selected_target",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {"card_type_in": ["artefatto"]},
                "min_targets": 0,
                "max_targets": 1,
            },
            "effect": {"action": "move_to_hand"},
        },
    ],
}
