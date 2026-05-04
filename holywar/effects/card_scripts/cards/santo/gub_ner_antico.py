from __future__ import annotations

CARD_NAME = """Gub-ner Antico"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "scripted",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_saint_defeated_in_battle", "frequency": "each_time"},
            "condition": {"event_card_name_is": "Token Gub-ner"},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "excommunicated",
                "owner": "any",
            },
            "effect": {"action": "choose_targets", "min_targets": 0, "max_targets": 1},
        },
        {
            "trigger": {"event": "on_saint_defeated_in_battle", "frequency": "each_time"},
            "condition": {"event_card_name_is": "Token Gub-ner"},
            "target": {
                "type": "selected_target",
                "zone": "excommunicated",
                "owner": "any",
                "min_targets": 0,
                "max_targets": 1,
            },
            "effect": {"action": "move_to_relicario"},
        },
        {
            "trigger": {"event": "on_saint_defeated_in_battle", "frequency": "each_time"},
            "condition": {"event_card_name_is": "Token Gub-ner"},
            "target": {
                "type": "selected_target",
                "zone": "deck",
                "owner": "any",
                "min_targets": 0,
                "max_targets": 1,
            },
            "effect": {"action": "shuffle_target_owner_decks"},
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
                "card_name": "Token Gub-ner",
                "owner": "me",
                "position": "selected_target_slot",
            },
        },
    ],
}
