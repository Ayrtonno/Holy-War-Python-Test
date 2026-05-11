from __future__ import annotations

CARD_NAME = "Lan Caihe"

SCRIPT = {
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
            "target": {"type": "source_card"},
            "effect": {"action": "store_top_card_of_zone", "owner": "me", "zone": "deck", "position": "top", "store_as": "lan_top"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "reveal_stored_card", "stored": "lan_top"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "move_stored_card_to_zone", "stored": "lan_top", "to_zone": "excommunicated"},
        },
        {
            "condition": {"stored_card_matches": {"stored": "lan_top", "card_filter": {"card_type_in": ["benedizione", "maledizione"]}}},
            "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"},
        },
        {
            "condition": {"stored_card_matches": {"stored": "lan_top", "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]}}},
            "target": {"type": "source_card"},
            "effect": {"action": "summon_stored_card_to_field", "stored": "lan_top"},
        },
        {
            "condition": {"stored_card_matches": {"stored": "lan_top", "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]}}},
            "target": {"type": "source_card"},
            "effect": {"action": "increase_strength", "amount": 3},
        },
    ],
}
