from __future__ import annotations

CARD_NAME = "Distorsione del Reliquiario"

SCRIPT = {
    "on_play_mode": "scripted",
    "on_enter_mode": "auto",
    "on_activate_mode": "auto",
    "play_targeting": "none",
    "triggered_effects": [],
    "on_play_actions": [
        {
            "effect": {
                "action": "move_all_from_zone_to_zone",
                "from_zone": "excommunicated",
                "to_zone": "relicario",
                "target_player": "me",
                "shuffle_after": True,
            }
        },
        {
            "effect": {
                "action": "move_all_from_zone_to_zone",
                "from_zone": "excommunicated",
                "to_zone": "relicario",
                "target_player": "opponent",
                "shuffle_after": True,
            }
        },
        {"effect": {"action": "draw_cards", "amount": 2, "target_player": "me"}},
        {"effect": {"action": "draw_cards", "amount": 2, "target_player": "opponent"}},
    ],
}
