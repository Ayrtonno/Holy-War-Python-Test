from __future__ import annotations

CARD_NAME = "Canti Religiosi"

SAINT_GRAVE_FILTER = {
    "card_type_in": ["santo", "token"],
}

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
                "action": "choose_option",
                "choice_title": "Canti Religiosi",
                "choice_prompt": "Scegli uno dei due effetti.",
                "choice_options": [
                    {
                        "value": "recover",
                        "label": "Riprendi un Santo dal cimitero",
                        "condition": {
                            "controller_has_cards": {
                                "zone": "graveyard",
                                "owner": "me",
                                "card_filter": SAINT_GRAVE_FILTER,
                            }
                        },
                    },
                    {
                        "value": "shield",
                        "label": "Annulla il primo attacco ricevuto nel turno",
                        "condition": {"my_saints_lte": 0},
                    },
                ],
            },
        },
        {
            "condition": {"selected_option_in": ["recover"]},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": SAINT_GRAVE_FILTER,
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "condition": {"selected_option_in": ["recover"]},
            "target": {
                "type": "selected_target",
                "zone": "graveyard",
                "owner": "me",
                "card_filter": SAINT_GRAVE_FILTER,
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "move_to_hand"},
        },
        {
            "condition": {"selected_option_in": ["recover"]},
            "target": {"type": "source_card"},
            "effect": {"action": "destroy_card"},
        },
        {
            "condition": {"selected_option_in": ["shield"]},
            "target": {"type": "source_card"},
            "effect": {"action": "set_attack_shield_this_turn", "target_player": "me"},
        },
    ],
}
