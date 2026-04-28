from __future__ import annotations

CARD_NAME = """Sacerdote Oroscopo"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_saint_defeated_in_battle",
                "frequency": "each_time",
                "condition": {"event_card_name_is": "Sacerdote Oroscopo"},
            },
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "deck",
                "owner": "me",
                "card_filter": {"card_type_in": ["benedizione"]},
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "trigger": {
                "event": "on_saint_defeated_in_battle",
                "frequency": "each_time",
                "condition": {"event_card_name_is": "Sacerdote Oroscopo"},
            },
            "target": {
                "type": "selected_target",
                "zone": "deck",
                "owner": "me",
                "card_filter": {"card_type_in": ["benedizione"]},
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "move_to_hand"},
        },
        {
            "trigger": {
                "event": "on_saint_defeated_in_battle",
                "frequency": "each_time",
                "condition": {"event_card_name_is": "Sacerdote Oroscopo"},
            },
            "target": {"type": "source_card"},
            "effect": {"action": "shuffle_deck", "target_player": "me"},
        },
    ],
    "on_play_actions": [],
}
