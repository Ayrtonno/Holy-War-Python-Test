from __future__ import annotations

CARD_NAME = "Terremoto: Magnitudo 10"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "any",
                "card_filter": {
                    "card_type_in": ["artefatto", "edificio"],
                },
            },
            "effect": {
                "action": "inflict_sin_to_target_owners",
                "amount": 2,
            },
        },
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "any",
                "card_filter": {
                    "card_type_in": ["artefatto", "edificio"],
                },
            },
            "effect": {
                "action": "send_to_graveyard",
            },
        },
        {
            "effect": {
                "action": "summon_card_from_hand",
                "card_name": "Vulcano",
            },
        },
        {
            "effect": {
                "action": "move_source_to_zone",
                "to_zone": "excommunicated",
            },
        },
    ],
}
