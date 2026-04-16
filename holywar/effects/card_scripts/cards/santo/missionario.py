from __future__ import annotations

CARD_NAME = 'Missionario'

SCRIPT = {
    "on_play_mode": "auto",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_owner": "opponent",
    "attack_targeting": "untargetable",
    "play_targeting": "none",
    "triggered_effects": [
        {
            "trigger": {"event": "on_my_turn_end", "frequency": "each_turn"},
            "condition": {"source_on_field": True},
            "target": {"type": "source_card"},
            "effect": {"action": "decrease_faith", "amount": 3},
        },
        {
            "trigger": {"event": "on_opponent_turn_end", "frequency": "each_turn"},
            "condition": {"source_on_field": True},
            "target": {"type": "source_card"},
            "effect": {"action": "decrease_faith", "amount": 3},
        },
        {
            "trigger": {"event": "on_saint_destroyed_by_effect", "frequency": "each_turn"},
            "condition": {
                "all_of": [
                    {"event_card_name_is": "Missionario"},
                    {"payload_reason_in": ["effect"]},
                ]
            },
            "target": {"type": "event_card"},
            "effect": {"action": "move_to_deck_bottom"},
        },
        {
            "trigger": {"event": "on_saint_destroyed_by_effect", "frequency": "each_turn"},
            "condition": {
                "all_of": [
                    {"event_card_name_is": "Missionario"},
                    {"payload_reason_in": ["effect"]},
                ]
            },
            "target": {"type": "event_card"},
            "effect": {"action": "shuffle_deck"},
        },
    ],
    "on_play_actions": [],
}
