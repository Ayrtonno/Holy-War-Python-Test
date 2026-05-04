from __future__ import annotations

CARD_NAME = "Gggnag'ljep"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "blocks_enemy_artifact_slots": 0,
    "triggered_effects": [],
    "on_play_actions": [
        {
            "effect": {
                "action": "choose_option",
                "choice_title": "Gggnag'ljep",
                "choice_prompt": "Scegli quale zona Artefatto avversaria bloccare.",
                "choice_options": [
                    {"value": "r1", "label": "Artefatto 1"},
                    {"value": "r2", "label": "Artefatto 2"},
                    {"value": "r3", "label": "Artefatto 3"},
                    {"value": "r4", "label": "Artefatto 4"},
                ],
            }
        },
        {
            "effect": {
                "action": "set_blocked_enemy_artifact_slot_from_selected_option",
            }
        },
    ],
}
