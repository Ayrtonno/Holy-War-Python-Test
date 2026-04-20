from __future__ import annotations

CARD_NAME = "Preghiera: Fertilità"


#Devo coddare l'esclusione dell'edificio se un edificio è già presente nel mio campo.
SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "guided",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "selected_target",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {
                    "name_contains": "Albero",
                },
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {
                "action": "summon_target_to_field",
                "exclude_buildings_if_my_building_zone_occupied": True,
            },
        },
        {
            "target": {
                "type": "selected_target",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {
                    "name_contains": "Albero",
                    "exclude_buildings_if_my_building_zone_occupied": True,
                },
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {
                "action": "move_to_hand",
            },
        },
        {
            "target": {
                "type": "selected_target",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {
                    "name_contains": "Albero",
                    "exclude_buildings_if_my_building_zone_occupied": True,
                },
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {
                "action": "excommunicate_card",
            },
        },
    ],
}