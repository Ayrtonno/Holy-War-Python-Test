from __future__ import annotations

CARD_NAME = "Ventaglio degli Otto Venti"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "scripted",
    "activate_once_per_turn": True,
    "play_targeting": "none",
    "activate_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [],
    "on_activate_actions": [
        {
            "effect": {
                "action": "choose_option",
                "choice_title": "Ventaglio degli Otto Venti",
                "choice_prompt": "Scegli un effetto.",
                "choice_options": [
                    {"label": "Pesca 1 carta", "value": "draw"},
                    {"label": "+4 Forza a un Ba Xian", "value": "buff"},
                    {"label": "Avversario scarta 1 dalla mano", "value": "discard"},
                ],
            }
        },
        {"condition": {"selected_option_in": ["draw"]}, "effect": {"action": "draw_cards", "amount": 1, "target_player": "me"}},
        {
            "condition": {"selected_option_in": ["buff"]},
            "target": {
                "type": "cards_controlled_by_owner",
                "zone": "field",
                "owner": "me",
                "card_filter": {"name_contains": "ba xian", "card_type_in": ["santo", "token"]},
            },
            "effect": {"action": "choose_targets", "min_targets": 1, "max_targets": 1},
        },
        {
            "condition": {"selected_option_in": ["buff"]},
            "target": {"type": "selected_target"},
            "effect": {"action": "increase_strength", "amount": 4},
        },
        {
            "condition": {"selected_option_in": ["discard"]},
            "target": {
                "type": "selected_target",
                "zone": "hand",
                "owner": "opponent",
                "min_targets": 1,
                "max_targets": 1,
            },
            "effect": {"action": "send_to_graveyard"},
        },
    ],
}
