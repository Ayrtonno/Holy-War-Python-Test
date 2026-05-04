from __future__ import annotations

CARD_NAME = """Manifestazione di Ph-Dak'Gaph"""

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [
        {
            "trigger": {"event": "on_card_excommunicated", "frequency": "each_time"},
            "target": {"type": "source_card"},
            "effect": {"action": "remove_sin", "amount": 2, "target_player": "me"},
        },
        {
            "trigger": {
                "event": "on_card_drawn",
                "frequency": "each_time",
                "condition": {"event_card_owner": "opponent"},
            },
            "target": {"type": "source_card"},
            "effect": {"action": "inflict_sin", "amount": 1, "target_player": "opponent"},
        },
        {
            "trigger": {"event": "on_this_card_leaves_field", "frequency": "each_time"},
            "target": {"type": "source_card"},
            "effect": {
                "action": "move_all_from_zone_to_zone",
                "from_zone": "excommunicated",
                "to_zone": "relicario",
                "target_player": "me",
            },
        },
        {
            "trigger": {"event": "on_this_card_leaves_field", "frequency": "each_time"},
            "target": {"type": "source_card"},
            "effect": {
                "action": "move_all_from_zone_to_zone",
                "from_zone": "excommunicated",
                "to_zone": "relicario",
                "target_player": "opponent",
            },
        },
        {
            "trigger": {"event": "on_this_card_leaves_field", "frequency": "each_time"},
            "target": {"type": "source_card"},
            "effect": {"action": "shuffle_deck", "target_player": "me"},
        },
        {
            "trigger": {"event": "on_this_card_leaves_field", "frequency": "each_time"},
            "target": {"type": "source_card"},
            "effect": {"action": "shuffle_deck", "target_player": "opponent"},
        },
    ],
    "on_enter_actions": [
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "excommunicated",
                "owner": "me",
                "card_filter": {"card_type_in": ["artefatto", "edificio", "santo"]},
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "target": {
                "type": "selected_target",
                "zone": "excommunicated",
                "owner": "me",
                "card_filter": {"card_type_in": ["artefatto", "edificio", "santo"]},
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "summon_target_to_field"},
        },
    ],
    "on_play_actions": [],
}
