from __future__ import annotations

CARD_NAME = "Custode della Creazione"

REQUIRED_DAYS = [
    "Giorno 1: Cieli e Terra",
    "Giorno 2: Cielo Terrestre",
    "Giorno 3: Terre e Mari",
    "Giorno 4: Stelle",
    "Giorno 5: Creature del Mare",
    "Giorno 6: Creature di Terra",
    "Giorno 7: Riposo",
]

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "play_requirements": {
        "all_of": [
            {
                "controller_has_cards": {
                    "zone": "graveyard",
                    "owner": "me",
                    "card_filter": {"name_equals": name},
                }
            }
            for name in REQUIRED_DAYS
        ]
    },
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": {"name_equals": name},
                "max_targets": 1,
            },
            "effect": {"action": "excommunicate_card_no_sin"},
        }
        for name in REQUIRED_DAYS
    ],
}
