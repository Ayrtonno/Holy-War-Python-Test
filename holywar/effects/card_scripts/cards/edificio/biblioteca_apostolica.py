from __future__ import annotations

CARD_NAME = "Biblioteca Apostolica"

SEARCH_FILTER = {
    "card_type_in": ["benedizione", "maledizione"],
}

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "play_targeting": "none",
    "activate_targeting": "guided",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_card_played",
                "frequency": "each_time",
                "condition": {"event_card_type_in": ["benedizione", "maledizione"]},
            },
            "target": { "target_policy": "optional_resolve", "selection_mode": "prompt", "cancel_behavior": "abort_step","type": "source_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "campana_add_counter"},
        },
    ],
    "on_play_actions": [
        { "activation_mode": "mandatory_auto","effect": {"action": "draw_cards", "amount": 0, "target_player": "me"}},
    ],
    "on_activate_actions": [
        {
            "activation_mode": "mandatory_auto",
            "condition": {"source_counter_gte": 3},
            "target": {
                "type": "selected_target",
                "zone": "deck",
                "owner": "me",
                "card_filter": SEARCH_FILTER,
                "min_targets": 1,
                "max_targets": 1,
                "target_policy": "required_to_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "move_to_hand"},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {"source_counter_gte": 3},
            "target": { "target_policy": "optional_resolve", "selection_mode": "prompt", "cancel_behavior": "abort_step","type": "source_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "campana_remove_counter", "amount": 3},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {"source_counter_gte": 3},
            "target": { "target_policy": "optional_resolve", "selection_mode": "prompt", "cancel_behavior": "abort_step","type": "source_card"},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            "effect": {"action": "shuffle_deck", "target_player": "me"},
        },
    ],
}
