from __future__ import annotations

CARD_NAME = 'Visioni Errate'

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {"type": "source_card"},
            "effect": {
                "action": "store_top_card_of_zone",
                "owner": "me",
                "zone": "deck",
                "position": "bottom",
                "store_as": "visioni_errate_bottom",
            },
        },
        {
            "target": {"type": "source_card"},
            "effect": {"action": "reveal_stored_card", "stored": "visioni_errate_bottom"},
        },
        {
            "target": {"type": "source_card"},
            "effect": {
                "action": "choose_option",
                "choice_title": "Visioni Errate",
                "choice_prompt": "Vuoi spostare questa carta in cima al tuo reliquiario?",
                "choice_options": [
                    {"id": "top", "label": "Sposta in cima"},
                    {"id": "bottom", "label": "Lasciala in fondo"},
                ],
            },
        },
        {
            "condition": {"selected_option_in": ["top"]},
            "target": {"type": "source_card"},
            "effect": {
                "action": "move_stored_card_to_zone",
                "stored": "visioni_errate_bottom",
                "to_zone": "deck",
            },
        },
    ],
}
