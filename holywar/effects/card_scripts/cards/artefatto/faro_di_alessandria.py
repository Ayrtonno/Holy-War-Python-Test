from __future__ import annotations

CARD_NAME = "Faro di Alessandria"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {
                "event": "on_card_drawn",
                "frequency": "each_turn",
                "condition": {"event_card_owner": "opponent"},
            },
            "target": {"type": "source_card"},
            "effect": {
                "action": "choose_option",
                "choice_title": "Faro di Alessandria",
                "choice_prompt": "L'avversario ha pescato una carta. Vuoi rimischiarla nel reliquiario e fargli pescare di nuovo?",
                "choice_options": [
                    {"id": "yes", "label": "Si"},
                    {"id": "no", "label": "No"},
                ],
            },
        },
        {
            "trigger": {
                "event": "on_card_drawn",
                "frequency": "each_turn",
                "condition": {"event_card_owner": "opponent"},
            },
            "condition": {"selected_option_in": ["yes"]},
            "target": {"type": "event_card"},
            "effect": {"action": "move_to_relicario"},
        },
        {
            "trigger": {
                "event": "on_card_drawn",
                "frequency": "each_turn",
                "condition": {"event_card_owner": "opponent"},
            },
            "condition": {"selected_option_in": ["yes"]},
            "target": {"type": "event_card"},
            "effect": {"action": "shuffle_target_owner_decks"},
        },
        {
            "trigger": {
                "event": "on_card_drawn",
                "frequency": "each_turn",
                "condition": {"event_card_owner": "opponent"},
            },
            "condition": {"selected_option_in": ["yes"]},
            "target": {"type": "source_card"},
            "effect": {"action": "draw_cards", "amount": 1, "target_player": "opponent"},
        },
    ],
    "on_play_actions": [],
}
