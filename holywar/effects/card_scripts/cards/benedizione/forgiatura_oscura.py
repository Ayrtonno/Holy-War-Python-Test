from __future__ import annotations

CARD_NAME = "Forgiatura Oscura"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "target": {
                "type": "cards_controlled_by_owner",
                "owner": "me",
                "zone": "relicario",
                "card_filter": {"card_type_in": ["artefatto"]},
            },
            "effect": {"action": "choose_targets_and_summon_to_field", "min_targets": 1, "max_targets": 1},
        },
        {
            "effect": {
                "action": "move_source_to_zone",
                "to_zone": "excommunicated",
            },
        },
    ],
}
