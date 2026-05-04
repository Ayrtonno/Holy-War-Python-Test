from __future__ import annotations

CARD_NAME = "Spiriti dell'Eternita"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "triggered_effects": [
        {
            "trigger": {"event": "on_this_card_receives_damage", "frequency": "each_time"},
            "target": {"type": "source_card"},
            "effect": {"action": "retaliate_event_damage_to_event_source_if_enemy_saint"},
        },
    ],
    "on_play_actions": [],
}
