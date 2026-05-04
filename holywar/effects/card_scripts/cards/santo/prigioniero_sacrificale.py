from __future__ import annotations

CARD_NAME = "Prigioniero Sacrificale"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_saint_defeated_or_destroyed",
                "frequency": "each_turn",
                "condition": {
                    "all_of": [
                        {"event_card_name_is": "Prigioniero Sacrificale"},
                        {"event_card_owner": "me"},
                    ]
                },
            },
            "target": {"type": "event_card"},
            "effect": {"action": "excommunicate_card_no_sin"},
        },
        {
            "trigger": {
                "event": "on_card_excommunicated",
                "frequency": "each_turn",
                "condition": {
                    "all_of": [
                        {"event_card_name_is": "Prigioniero Sacrificale"},
                        {"event_card_owner": "me"},
                    ]
                },
            },
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "hand",
                "owner": "me",
            },
            "effect": {"action": "choose_targets", "min_targets": 0, "max_targets": 3},
        },
        {
            "trigger": {
                "event": "on_card_excommunicated",
                "frequency": "each_turn",
                "condition": {
                    "all_of": [
                        {"event_card_name_is": "Prigioniero Sacrificale"},
                        {"event_card_owner": "me"},
                    ]
                },
            },
            "target": {"type": "selected_targets"},
            "effect": {"action": "store_target_count", "flag": "prigioniero_sacrificale_cards_moved"},
        },
        {
            "trigger": {
                "event": "on_card_excommunicated",
                "frequency": "each_turn",
                "condition": {
                    "all_of": [
                        {"event_card_name_is": "Prigioniero Sacrificale"},
                        {"event_card_owner": "me"},
                    ]
                },
            },
            "target": {"type": "selected_targets"},
            "effect": {"action": "move_to_relicario"},
        },
        {
            "trigger": {
                "event": "on_card_excommunicated",
                "frequency": "each_turn",
                "condition": {
                    "all_of": [
                        {"event_card_name_is": "Prigioniero Sacrificale"},
                        {"event_card_owner": "me"},
                    ]
                },
            },
            "target": {"type": "source_card"},
            "effect": {
                "action": "draw_cards_from_flag",
                "flag": "prigioniero_sacrificale_cards_moved",
                "target_player": "me",
            },
        },
    ],
    "on_play_actions": [],
}
