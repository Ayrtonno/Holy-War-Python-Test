from __future__ import annotations

CARD_NAME = "Lan Caihe"

SOURCE_TARGET = {
    "type": "source_card",
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
    "on_play_mode": "auto",
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
            "target": SOURCE_TARGET,
            "effect": {"action": "store_top_card_of_zone", "owner": "me", "zone": "deck", "position": "top", "store_as": "lan_top"},
        },
        {
            "activation_mode": "mandatory_auto",
            "target": SOURCE_TARGET,
            "effect": {"action": "reveal_stored_card", "stored": "lan_top"},
        },
        {
            "activation_mode": "mandatory_auto",
            "target": SOURCE_TARGET,
            "effect": {"action": "move_stored_card_to_zone", "stored": "lan_top", "to_zone": "excommunicated"},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {"stored_card_matches": {"stored": "lan_top", "card_filter": {"card_type_in": ["benedizione", "maledizione"]}}},
            "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {"stored_card_matches": {"stored": "lan_top", "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]}}},
            "target": SOURCE_TARGET,
            "effect": {"action": "summon_stored_card_to_field", "stored": "lan_top", "placement_policy": "prompt_slot_required"},
        },
        {
            "activation_mode": "mandatory_auto",
            "condition": {"stored_card_matches": {"stored": "lan_top", "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]}}},
            "target": SOURCE_TARGET,
            "effect": {"action": "increase_strength", "amount": 3},
        },
    ],
}

