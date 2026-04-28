from __future__ import annotations

CARD_NAME = """Gub-ner Antico"""

SCRIPT = {
    "on_play_mode": "noop",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_enter_field", "frequency": "each_time"},
            "condition": {"event_card_name_is": "Gub-ner Antico"},
            "target": {"type": "source_card"},
            "effect": {
                "action": "choose_option",
                "choice_title": "Gub-ner Antico",
                "choice_prompt": "Vuoi evocare un Token Gub-ner?",
                "options": [
                    {"value": "yes", "label": "Si"},
                    {"value": "no", "label": "No"},
                ],
            },
        },
        {
            "trigger": {"event": "on_enter_field", "frequency": "each_time"},
            "condition": {
                "all_of": [
                    {"event_card_name_is": "Gub-ner Antico"},
                    {"selected_option_in": ["yes"]},
                ]
            },
            "target": {"type": "source_card"},
            "effect": {"action": "summon_generated_token", "card_name": "Token Gub-ner"},
        },
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
}
