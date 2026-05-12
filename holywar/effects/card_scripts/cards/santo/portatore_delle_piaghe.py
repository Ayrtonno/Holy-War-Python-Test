from __future__ import annotations

CARD_NAME = "Portatore delle Piaghe"

SCRIPT = {
    "default_selection_mode": "prompt",
    "default_cancel_behavior": "abort_step",
    "default_target_policy": "optional_resolve",
    "default_placement_policy": "prompt_slot_required",
    "default_activation_mode": "mandatory_auto",
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "activate_once_per_turn": True,
    "play_targeting": "none",
    "activate_targeting": "none",
    "play_requirements": {
        "can_play_by_sacrificing": {
            "owner": "me",
            "zone": "hand",
            "zones": ["hand", "graveyard"],
            "count": 3,
            "card_filter": {
                "name_contains": "piaga",
            },
        },
        "choose_play_sacrifices_from_target": True,
        "can_play_without_inspiration_cost_if": {
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
        "play_sacrifices_to_zone": "excommunicated",
        "play_sacrifices_no_sin_on_death": True,
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
    "on_play_actions": [],
    "on_activate_actions": [
        {
            "activation_mode": "mandatory_auto",
            "target": { "target_policy": "optional_resolve", "selection_mode": "prompt", "cancel_behavior": "abort_step","type": "source_card"},
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
                "target_policy": "optional_resolve",
                "selection_mode": "prompt",
                "cancel_behavior": "abort_step",
            },
        }
    ],
}
