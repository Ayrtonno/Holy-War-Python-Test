from __future__ import annotations

CARD_NAME = "Mela del Peccato"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "guided",
    "triggered_effects": [
        {
            "trigger": {"event": "on_saint_defeated_or_destroyed", "frequency": "each_turn"},
            "target": {"type": "source_card"},
            "effect": {"action": "inflict_sin_to_event_owner_equal_base_faith_if_equipped_target"},
        },
        {
            "trigger": {"event": "on_saint_defeated_or_destroyed", "frequency": "each_turn"},
            "target": {"type": "source_card"},
            "effect": {"action": "move_source_to_zone_if_equipped_target_is_event_card", "to_zone": "excommunicated"},
        },
    ],
    "on_play_actions": [
        {
            "target": {
                "type": "selected_target",
                "owner": "me",
                "zone": "field",
                "card_filter": {"card_type_in": ["santo", "token"]},
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "equip_card"},
        },
        {
            "target": {"type": "equipped_target_of_source"},
            "effect": {"action": "increase_faith", "amount": 15},
        },
    ],
}
