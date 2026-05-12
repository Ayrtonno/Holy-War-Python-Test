from __future__ import annotations

CARD_NAME = "Padiglione degli Immortali"

SOURCE_TARGET = {
    "type": "source_card",
    "target_policy": "optional_resolve",
    "selection_mode": "prompt",
    "cancel_behavior": "abort_step",
}

SELECTED_TARGET = {
    "type": "selected_target",
    "target_policy": "optional_resolve",
    "selection_mode": "prompt",
    "cancel_behavior": "abort_step",
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
    "activate_targeting": "none",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_summoned_from_hand",
                "frequency": "each_time",
                "condition": {"event_card_owner": "me", "event_card_name_contains": "ba xian", "event_card_type_in": ["santo"]},
            },
            "target": SOURCE_TARGET,
            "effect": {"action": "campana_add_counter"},
        },
        {
            "trigger": {
                "event": "on_summoned_from_relicario",
                "frequency": "each_time",
                "condition": {"event_card_owner": "me", "event_card_name_contains": "ba xian", "event_card_type_in": ["santo"]},
            },
            "target": SOURCE_TARGET,
            "effect": {"action": "campana_add_counter"},
        },
        {
            "trigger": {
                "event": "on_summoned_from_graveyard",
                "frequency": "each_time",
                "condition": {"event_card_owner": "me", "event_card_name_contains": "ba xian", "event_card_type_in": ["santo"]},
            },
            "target": SOURCE_TARGET,
            "effect": {"action": "campana_add_counter"},
        },
    ],
    "on_play_actions": [],
    "on_activate_actions": [
        {
            "activation_mode": "mandatory_auto",
            "condition": {"source_counter_gte": 3},
            "effect": {
                "action": "choose_option",
                "choice_title": "Padiglione",
                "choice_prompt": "Scegli.",
                "choice_options": [
                    {"label": "Pesca 1", "value": "draw"},
                    {
                        "label": "Ba Xian dal cimitero",
                        "value": "recover",
                        "condition": {
                            "controller_has_cards": {
                                "zone": "graveyard",
                                "owner": "me",
                                "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo"]},
                                "min_count": 1,
                            }
                        },
                    },
                ],
            },
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {"all_of": [{"source_counter_gte": 3}, {"selected_option_in": ["draw"]}]},
            "target": SOURCE_TARGET,
            "effect": {"action": "campana_remove_counter", "amount": 3},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {"all_of": [{"source_counter_gte": 3}, {"selected_option_in": ["draw"]}]},
            "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {"all_of": [{"source_counter_gte": 3}, {"selected_option_in": ["recover"]}]},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo"]},
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {"all_of": [{"source_counter_gte": 3}, {"selected_option_in": ["recover"]}, {"selected_target_exists": True}]},
            "target": SELECTED_TARGET,
            "effect": {"action": "move_to_hand"},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {"all_of": [{"source_counter_gte": 3}, {"selected_option_in": ["recover"]}, {"selected_target_exists": True}]},
            "target": SOURCE_TARGET,
            "effect": {"action": "campana_remove_counter", "amount": 3},
        },
    ],
}

