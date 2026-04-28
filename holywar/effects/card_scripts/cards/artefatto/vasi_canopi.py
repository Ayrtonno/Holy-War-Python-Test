from __future__ import annotations

CARD_NAME = "Vasi Canopi"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "guided",
    "triggered_effects": [
        {
            "trigger": {"event": "on_saint_defeated_or_destroyed", "frequency": "each_turn"},
            "target": {"type": "equipped_target_of_source"},
            "effect": {"action": "summon_target_to_field"},
        },
        {
            "trigger": {"event": "on_saint_defeated_or_destroyed", "frequency": "each_turn"},
            "target": {"type": "source_card"},
            "effect": {"action": "destroy_source_if_equipped_target_is_event_card"},
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
        }
    ],
}
