from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from holywar.core.engine import GameEngine

# This module defines functions for managing runtime state flags in the game engine. The runtime state includes information about the current phase of the game, which player's turn it is, and various flags that indicate what actions are currently allowed for each player. The `ensure_runtime_state` function initializes the runtime state if it doesn't already exist, while the `refresh_player_flags` function updates the player-specific flags based on the current game state. The `set_phase` function is used to update the current phase of the game and refresh the player flags accordingly.
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

# This function ensures that the runtime state dictionary exists in the game engine's state flags and initializes it with default values if it doesn't already exist. It sets up various flags related to the current phase of the game, which player's turn it is, and other state information that will be used throughout the game. The function returns the runtime state dictionary for further manipulation.
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

# This function updates the player-specific flags in the runtime state based on the current game state. It iterates through each player and sets flags indicating whether they are the turn owner, whether it's their opponent's turn, which phase of the game it is, and what actions they are allowed to take (e.g., playing cards, activating effects, attacking). It also updates counts of saints on the field and in attack/defense positions, as well as remaining inspiration and sin for each player. This function should be called whenever there is a change in the game state that affects these flags, such as changing phases or updating the active player.
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

# This function is responsible for updating the current phase of the game in the runtime state and refreshing the player flags accordingly. It takes the game engine and the new phase as arguments, updates the relevant flags in the runtime state to reflect the new phase, and then calls `refresh_player_flags` to ensure that all player-specific flags are updated based on the new phase. This function should be called whenever there is a transition to a new phase in the game (e.g., from draw phase to main phase) to keep the runtime state consistent with the current game state.
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
