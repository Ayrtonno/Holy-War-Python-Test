from __future__ import annotations

CARD_NAME = """Albero Sacro"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "scripted",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "auto_play_on_draw": True,
    "end_turn_on_draw": True,
    "triggered_effects": [
        {
            "trigger": {"event": "on_preparation_complete", "frequency": "each_turn"},
            "target": {"type": "empty_saint_slots_controlled_by_owner", "owner": "me"},
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "trigger": {"event": "on_preparation_complete", "frequency": "each_turn"},
            "target": {"type": "source_card"},
            "effect": {
                "action": "summon_generated_token",
                "card_name": "Token Albero",
                "owner": "me",
                "position": "selected_target_slot",
            },
        },
        {
            "trigger": {"event": "on_my_turn_end", "frequency": "each_turn"},
            "target": {"type": "empty_saint_slots_controlled_by_owner", "owner": "me"},
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "trigger": {"event": "on_opponent_turn_end", "frequency": "each_turn"},
            "target": {"type": "empty_saint_slots_controlled_by_owner", "owner": "me"},
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "trigger": {"event": "on_my_turn_end", "frequency": "each_turn"},
            "target": {"type": "source_card"},
            "effect": {
                "action": "summon_generated_token",
                "card_name": "Token Albero",
                "owner": "me",
                "position": "selected_target_slot",
            },
        },
        {
            "trigger": {"event": "on_opponent_turn_end", "frequency": "each_turn"},
            "target": {"type": "source_card"},
            "effect": {
                "action": "summon_generated_token",
                "card_name": "Token Albero",
                "owner": "me",
                "position": "selected_target_slot",
            },
        },
        {
            "trigger": {"event": "on_saint_defeated_in_battle", "frequency": "each_turn"},
            "condition": {"event_card_name_is": "Token Albero"},
            "target": {"type": "source_card"},
            "effect": {"action": "increase_faith", "amount": 2},
        },
    ],
    "on_play_actions": [],
    "on_enter_actions": [
        {
            "target": {"type": "empty_saint_slots_controlled_by_owner", "owner": "me"},
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "target": {"type": "source_card"},
            "effect": {
                "action": "summon_generated_token",
                "card_name": "Token Albero",
                "owner": "me",
                "position": "selected_target_slot",
            },
        },
    ],
}
