from __future__ import annotations

CARD_NAME = """Paladino Corrotto"""

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
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
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
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
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"},
        }
    ],
    "on_play_actions": [],
}
