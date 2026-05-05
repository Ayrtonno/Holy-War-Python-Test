from __future__ import annotations

CARD_NAME = "Portatore delle Piaghe"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "activate_once_per_turn": True,
    "play_targeting": "guided",
    "activate_targeting": "none",
    "play_requirements": {
        "controller_has_cards": {
            "owner": "me",
            "zone": "hand",
            "zones": ["hand", "graveyard"],
            "min_count": 3,
            "card_filter": {
                "name_contains": "piaga",
            },
        }
    },
    "protection_rules": [
        {
            "event": "target_by_effect",
            "source_owner": "any",
            "target_owner": "any",
            "target_names": ["Portatore delle Piaghe"],
        }
    ],
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "selected_targets",
                "owner": "me",
                "zone": "hand",
                "zones": ["hand", "graveyard"],
                "card_filter": {"name_contains": "piaga"},
                "min_targets": 3,
                "max_targets": 3,
            },
            "effect": {"action": "excommunicate_card_no_sin"},
        }
    ],
    "on_activate_actions": [
        {
            "target": {"type": "source_card"},
            "effect": {
                "action": "choose_and_activate_effect",
                "target_player": "me",
                "choice_title": "Portatore delle Piaghe",
                "choice_prompt": "Scegli una carta Piaga (Benedizione/Maledizione) da cui copiare l'effetto.",
                "choice_options": [
                    {
                        "candidate_source": "initial_deck",
                        "zones": ["deck", "graveyard", "excommunicated"],
                        "name_contains": "piaga",
                        "card_type_in": ["benedizione", "maledizione"],
                    }
                ],
            },
        }
    ],
}
