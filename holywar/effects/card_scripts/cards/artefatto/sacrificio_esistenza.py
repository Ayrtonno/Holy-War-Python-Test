from __future__ import annotations

CARD_NAME = "Sacrificio: Esistenza"

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
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
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
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
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
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
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "remove_sin", "target_player": "me", "amount": 3},
        },
    ],
    "on_play_actions": [],
}
