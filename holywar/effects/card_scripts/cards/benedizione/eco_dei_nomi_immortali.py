from __future__ import annotations

CARD_NAME = "Eco dei Nomi Immortali"

HAS_1 = {
    "controller_has_cards": {
        "zones": ["hand"],
        "owner": "me",
        "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
        "min_count": 1,
    }
}
HAS_2 = {
    "controller_has_cards": {
        "zones": ["hand"],
        "owner": "me",
        "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
        "min_count": 2,
    }
}
HAS_3 = {
    "controller_has_cards": {
        "zones": ["hand"],
        "owner": "me",
        "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
        "min_count": 3,
    }
}

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "auto",
    "triggered_effects": [],
    "on_play_actions": [
        { "activation_mode": "mandatory_auto","condition": HAS_1, "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"}},
        { "activation_mode": "mandatory_auto","condition": HAS_2, "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"}},
        { "activation_mode": "mandatory_auto","condition": HAS_3, "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"}},
        {
            "activation_mode": "mandatory_auto",
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "hand",
                "owner": "me",
                "card_filter": {"exclude_event_card": True},
                "min_targets": 1,
                "max_targets": 1,
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "activation_mode": "mandatory_auto",
            "target": { "target_policy": "optional_resolve", "selection_mode": "prompt", "cancel_behavior": "abort_step","type": "selected_target"},
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "move_to_relicario"},
        },
        { "activation_mode": "mandatory_auto","effect": {"action": "shuffle_deck", "target_player": "me"}},
    ],
}
