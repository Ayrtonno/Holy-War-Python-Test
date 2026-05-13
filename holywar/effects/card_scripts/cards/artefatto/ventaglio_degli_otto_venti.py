from __future__ import annotations

CARD_NAME = "Ventaglio degli Otto Venti"

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "activate_once_per_turn": True,
    "play_targeting": "none",
    "activate_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [],
    "on_activate_actions": [
        {
            "activation_mode": "mandatory_auto",
            "effect": {
                "action": "choose_option",
                "choice_title": "Ventaglio degli Otto Venti",
                "choice_prompt": "Scegli un effetto.",
                "choice_options": [
                    {"label": "Pesca 1 carta", "value": "draw"},
                    {"label": "+4 Forza a un Ba Xian", "value": "buff"},
                    {"label": "Avversario scarta 1 dalla mano", "value": "discard"},
                ],
            }
        },
        { "activation_mode": "mandatory_auto","condition": {"selected_option_in": ["draw"]}, "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"}},
        {
            "activation_mode": "mandatory_auto",
            "condition": {"selected_option_in": ["buff"]},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {"selected_option_in": ["buff"]},
            "target": {
                "type": "selected_target",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "increase_strength", "amount": 4},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {"selected_option_in": ["discard"]},
            "target": {
                "type": "selected_target",
                "zone": "hand",
                "owner": "opponent",
                "min_targets": 1,
                "max_targets": 1,
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "send_to_graveyard"},
        },
    ],
}
