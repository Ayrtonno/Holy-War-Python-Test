from __future__ import annotations

CARD_NAME = "Assalto Gub-ner"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "activate_once_per_turn": True,
    "activate_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [],
    "on_activate_actions": [
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"card_type_in": ["token"], "name_contains": "Gub-ner"},
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "target": {
                "type": "selected_target",
                "zone": "field",
                "owner": "me",
                "card_filter": {"card_type_in": ["token"], "name_contains": "Gub-ner"},
                "min_targets": 0,
                "max_targets": 1,
            },
            "effect": {"action": "destroy_card"},
        },
        {
            "condition": {"selected_target_exists": True},
            "target": {"type": "cards_controlled_by_owner", "zone": "field", "owner": "opponent"},
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "condition": {"selected_target_exists": True},
            "target": {"type": "selected_target", "zone": "field", "owner": "opponent", "min_targets": 0, "max_targets": 1},
            "effect": {"action": "destroy_card"},
        },
    ],
}
