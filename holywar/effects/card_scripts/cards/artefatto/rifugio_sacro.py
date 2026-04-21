from __future__ import annotations

CARD_NAME = "Rifugio Sacro"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "prevent_incoming_damage_if_less_than": 3,
    "prevent_incoming_damage_to_card_types": ["santo", "token"],
    "triggered_effects": [],
    "on_play_actions": [],
}
