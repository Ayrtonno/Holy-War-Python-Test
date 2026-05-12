from __future__ import annotations

CARD_NAME = "Albero Fortunato"

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
            "trigger": {
                "event": "on_card_sent_to_graveyard",
                "condition": {
                    "event_card_name_is": "Albero Fortunato",
                    "event_card_owner": "me",
                    "payload_from_zone_in": ["attack", "defense", "field"],
                },
            },
            "condition": {
                "event_card_name_is": "Albero Fortunato",
                "event_card_owner": "me",
                "payload_from_zone_in": ["attack", "defense", "field"],
            },
            "target": {
                "type": "source_card",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {
                "action": "draw_cards",
                "amount": 2,
                "target_player": "me",
            },
        }
    ],
    "on_play_actions": [],
}
