from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from holywar.core.engine import GameEngine


def _player_template() -> dict[str, Any]:
    return {
        "is_turn_owner": False,
        "is_opponent_turn_owner": False,
        "is_draw_phase": False,
        "is_main_phase": False,
        "is_battle_phase": False,
        "is_end_phase": False,
        "can_play_cards": False,
        "can_activate_effects": False,
        "can_attack": False,
        "can_reposition_saints": False,
        "saints_on_field": 0,
        "saints_in_attack": 0,
        "saints_in_defense": 0,
        "remaining_inspiration": 0,
        "sin": 0,
    }


def ensure_runtime_state(engine: "GameEngine") -> dict[str, Any]:
    root = engine.state.flags.setdefault("runtime_state", {})
    root.setdefault("phase", "setup")
    root.setdefault("turn_owner", int(engine.state.active_player))
    root.setdefault("is_turn_start_window", False)
    root.setdefault("is_draw_phase", False)
    root.setdefault("is_main_phase", False)
    root.setdefault("is_battle_phase", False)
    root.setdefault("is_end_phase", False)
    root.setdefault("is_action_window_open", False)
    root.setdefault("is_target_selection_open", False)
    root.setdefault("is_stack_resolving", False)
    root.setdefault("is_resolution_atomic", False)
    root.setdefault("battle_phase_started", False)
    players = root.setdefault("players", {"0": _player_template(), "1": _player_template()})
    for idx in ("0", "1"):
        players.setdefault(idx, _player_template())
    return root


def refresh_player_flags(engine: "GameEngine") -> None:
    root = ensure_runtime_state(engine)
    players = root["players"]
    turn_owner = int(engine.state.active_player)
    for idx in (0, 1):
        p = engine.state.players[idx]
        key = str(idx)
        state = players.setdefault(key, _player_template())
        state["is_turn_owner"] = idx == turn_owner
        state["is_opponent_turn_owner"] = idx != turn_owner
        state["is_draw_phase"] = bool(root["is_draw_phase"])
        state["is_main_phase"] = bool(root["is_main_phase"])
        state["is_battle_phase"] = bool(root["is_battle_phase"])
        state["is_end_phase"] = bool(root["is_end_phase"])
        state["can_play_cards"] = bool(root["is_main_phase"])
        state["can_activate_effects"] = bool(root["is_main_phase"] or root["is_battle_phase"])
        state["can_attack"] = bool(root["is_battle_phase"])
        state["can_reposition_saints"] = bool(root["is_main_phase"] and not root["is_battle_phase"])
        attack = [uid for uid in p.attack if uid is not None]
        defense = [uid for uid in p.defense if uid is not None]
        state["saints_in_attack"] = len(attack)
        state["saints_in_defense"] = len(defense)
        state["saints_on_field"] = len(engine.all_saints_on_field(idx))
        state["remaining_inspiration"] = int(p.inspiration)
        state["sin"] = int(p.sin)


def set_phase(engine: "GameEngine", phase: str) -> None:
    root = ensure_runtime_state(engine)
    root["phase"] = phase
    root["is_turn_start_window"] = phase == "turn_start"
    root["is_draw_phase"] = phase == "draw"
    root["is_main_phase"] = phase == "main"
    root["is_battle_phase"] = phase == "battle"
    root["is_end_phase"] = phase == "end"
    root["is_action_window_open"] = phase in {"main", "battle"}
    refresh_player_flags(engine)
