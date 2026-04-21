from __future__ import annotations

import unicodedata
from typing import TYPE_CHECKING

from holywar.core.state import TURN_INSPIRATION, MAX_HAND
from holywar.effects.runtime import EffectSpec, runtime_cards
from holywar.effects.state_flags import ensure_runtime_state, refresh_player_flags, set_phase

if TYPE_CHECKING:
    from holywar.core.engine import GameEngine


def _norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", text)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


# Performs the initial setup draw for both players at match start.
def initial_setup_draw(engine: "GameEngine") -> None:
    for idx in (0, 1):
        draw_cards(engine, idx, 5)
    engine.state.flags.setdefault("cards_drawn_this_turn", {"0": [], "1": []})["0"] = []
    engine.state.flags.setdefault("cards_drawn_this_turn", {"0": [], "1": []})["1"] = []
    engine.state.flags.setdefault("saints_sent_to_graveyard_this_turn", {"0": 0, "1": 0})["0"] = 0
    engine.state.flags.setdefault("saints_sent_to_graveyard_this_turn", {"0": 0, "1": 0})["1"] = 0
    engine.state.log("Setup iniziale completato: entrambi i giocatori hanno pescato 5 carte.")


# Draws cards while applying draw-triggered effects and bookkeeping.
def draw_cards(engine: "GameEngine", player_idx: int, amount: int) -> int:
    player = engine.state.players[player_idx]
    drawn = 0
    for _ in range(amount):
        if len(player.hand) >= MAX_HAND:
            break
        if not player.deck:
            break
        drawn_uid = player.deck.pop()
        player.hand.append(drawn_uid)
        drawn += 1
        engine.state.flags.setdefault("cards_drawn_this_turn", {"0": [], "1": []}).setdefault(str(player_idx), []).append(drawn_uid)
        engine._emit_event("on_card_drawn", player_idx, card=drawn_uid, from_zone="relicario")
        card_name = engine.state.instances[drawn_uid].definition.name
        if runtime_cards.get_auto_play_on_draw(card_name):
            flags = engine.state.flags
            previous_source = flags.get("_runtime_source_card")
            previous_selected = flags.get("_runtime_selected_target")
            flags["_runtime_source_card"] = drawn_uid
            flags["_runtime_selected_target"] = ""
            try:
                runtime_cards._apply_effect(engine, player_idx, drawn_uid, [drawn_uid], EffectSpec(action="move_source_to_board"))
            finally:
                if previous_source is None:
                    flags.pop("_runtime_source_card", None)
                else:
                    flags["_runtime_source_card"] = previous_source
                if previous_selected is None:
                    flags.pop("_runtime_selected_target", None)
                else:
                    flags["_runtime_selected_target"] = previous_selected
        if runtime_cards.get_end_turn_on_draw(card_name):
            engine.state.flags.setdefault("runtime_state", {})["request_end_turn"] = True
        engine._emit_event("after_card_drawn_from_deck", player_idx, card=drawn_uid)
        engine._emit_event("on_opponent_draws", 1 - player_idx, card=drawn_uid, opponent=player_idx)
    refresh_player_flags(engine)
    return drawn


# Resets resources and per-turn board state for the active player.
def _reset_start_turn_resources(engine: "GameEngine", current: int) -> None:
    player = engine.state.players[current]
    player.inspiration = TURN_INSPIRATION
    bonus_next = engine.state.flags.setdefault("bonus_inspiration_next_turn", {"0": 0, "1": 0})
    key = str(engine.state.active_player)
    player.inspiration += int(bonus_next.get(key, 0))
    bonus_next[key] = 0
    for uid in player.attack:
        if uid:
            engine.state.instances[uid].exhausted = False


# Summons start-of-turn support tokens behind saints when their scripts require it.
def _summon_turn_start_tokens(engine: "GameEngine", current: int) -> None:
    player = engine.state.players[current]
    for i, a_uid in enumerate(player.attack):
        if not a_uid:
            continue
        token_name = runtime_cards.get_turn_start_summon_token_name(engine.state.instances[a_uid].definition.name)
        if not token_name:
            continue
        def_uid = player.defense[i]
        if def_uid and _norm(engine.state.instances[def_uid].definition.name) == _norm(token_name):
            continue
        token_uid = None
        for pool_name in ("white_deck", "deck", "graveyard", "excommunicated"):
            pool = getattr(player, pool_name)
            for c_uid in list(pool):
                if _norm(engine.state.instances[c_uid].definition.name) != _norm(token_name):
                    continue
                pool.remove(c_uid)
                token_uid = c_uid
                break
            if token_uid:
                break
        if token_uid is not None and player.defense[i] is None:
            player.defense[i] = token_uid
            engine.state.log(f"{player.name} evoca {token_name} dietro {engine.state.instances[a_uid].definition.name}.")


# Resolves the active player's draw phase, including special draw modifiers.
def _run_draw_phase(engine: "GameEngine", current: int) -> int:
    player = engine.state.players[current]
    next_draw_override = engine.state.flags.setdefault("next_turn_draw_override", {"0": 0, "1": 0})
    override_amount = int(next_draw_override.get(str(engine.state.active_player), 0) or 0)
    if override_amount > 0:
        next_draw_override[str(engine.state.active_player)] = 0
        return draw_cards(engine, engine.state.active_player, override_amount)

    spore_pending = engine.state.flags.setdefault("spore_pending", {"0": False, "1": False})
    if spore_pending.get(str(engine.state.active_player), False):
        drawn = draw_cards(engine, engine.state.active_player, 8)
        spore_pending[str(engine.state.active_player)] = False
        return drawn

    bonus_draw = 0
    pyramid_count = sum(
        1
        for uid in player.artifacts
        if uid and _norm(engine.state.instances[uid].definition.name) in {
            _norm("Piramide: Chefren"),
            _norm("Piramide: Cheope"),
            _norm("Piramide: Micerino"),
        }
    )
    if pyramid_count >= 3:
        bonus_draw += 2
    return draw_cards(engine, engine.state.active_player, 3 + bonus_draw)


# Starts the active player's turn and advances the game into the main phase when appropriate.
def start_turn(engine: "GameEngine") -> None:
    current = engine.state.active_player
    player = engine.state.players[current]
    runtime_state = ensure_runtime_state(engine)
    runtime_state["battle_phase_started"] = False
    double_next = engine.state.flags.setdefault("double_cost_next_turn", {"0": 0, "1": 0})
    pending_double = int(double_next.get(str(current), 0) or 0)
    # "Next turn" cost taxes must start only on real active turns, never during preparation.
    if pending_double > 0 and engine.state.phase != "preparation":
        double_turns = engine.state.flags.setdefault("double_cost_turns", {"0": 0, "1": 0})
        double_turns[str(current)] = int(double_turns.get(str(current), 0)) + pending_double
        double_next[str(current)] = 0
    engine.state.flags.setdefault("saints_sent_to_graveyard_this_turn", {"0": 0, "1": 0})["0"] = 0
    engine.state.flags.setdefault("saints_sent_to_graveyard_this_turn", {"0": 0, "1": 0})["1"] = 0
    set_phase(engine, "turn_start")
    engine._emit_event("on_turn_start", current, player=current)
    engine._emit_event("on_my_turn_start", current, player=current)
    engine._emit_event("on_opponent_turn_start", 1 - current, opponent=current)
    set_phase(engine, "draw")
    engine._emit_event("before_draw_phase", current, player=current)
    engine._emit_event("on_draw_phase_start", current, player=current)

    _reset_start_turn_resources(engine, current)
    _summon_turn_start_tokens(engine, current)
    engine.state.flags.setdefault("attack_count", {"0": 0, "1": 0})[str(engine.state.active_player)] = 0
    engine.state.flags["attacked_targets_this_turn"] = {}
    engine.state.flags.setdefault("spent_inspiration_turn", {"0": 0, "1": 0})[str(engine.state.active_player)] = 0
    engine._cleanup_zero_faith_saints()
    if engine.state.phase == "preparation":
        engine.state.log(
            f"Preparazione: {player.name} dispone di 10 Ispirazione e non puo attaccare."
        )
        return

    drawn = _run_draw_phase(engine, current)
    engine._emit_event("on_draw_phase_end", current, player=current, drawn=drawn)
    set_phase(engine, "main")
    engine._emit_event("on_main_phase_start", current, player=current)
    engine.state.log(f"Turno {engine.state.turn_number}: {player.name} pesca {drawn} carte e ottiene 10 Ispirazione.")
    refresh_player_flags(engine)


# Completes end-of-turn effects and hands control to the next player or phase.
def end_turn(engine: "GameEngine") -> None:
    current = engine.state.active_player
    runtime_state = ensure_runtime_state(engine)
    if bool(runtime_state.get("battle_phase_started", False)):
        set_phase(engine, "battle")
        engine._emit_event("on_battle_phase_end", current, player=current)
        runtime_state["battle_phase_started"] = False
    set_phase(engine, "end")
    engine._emit_event("on_main_phase_end", current, player=current)
    engine._emit_event("on_turn_end", current, player=current)
    engine._emit_event("on_my_turn_end", current, player=current)
    engine._emit_event("on_opponent_turn_end", 1 - current, opponent=current)
    engine.state.flags.setdefault("cards_drawn_this_turn", {"0": [], "1": []})[str(current)] = []
    engine._cleanup_zero_faith_saints()
    engine.check_win_conditions()
    if engine.state.winner is not None:
        return
    if engine.state.phase == "preparation":
        engine.state.preparation_turns_done += 1
        if engine.state.preparation_turns_done >= 2:
            engine.state.phase = "active"
            engine.state.coin_toss_winner = engine.rng.randint(0, 1)
            engine.state.active_player = engine.state.coin_toss_winner
            engine.state.turn_number = 1
            engine.state.log(
                f"Fine preparazione: lancio moneta -> inizia {engine.state.players[engine.state.active_player].name}."
            )
            set_phase(engine, "setup")
            refresh_player_flags(engine)
            engine._reset_effect_usage_this_turn()
            engine._reset_turn_once_markers_this_turn()
            return
        engine.state.active_player = 1 - engine.state.active_player
        set_phase(engine, "setup")
        refresh_player_flags(engine)
        engine._reset_effect_usage_this_turn()
        engine._reset_turn_once_markers_this_turn()
        return
    double_turns = engine.state.flags.setdefault("double_cost_turns", {"0": 0, "1": 0})
    key = str(engine.state.active_player)
    if int(double_turns.get(key, 0)) > 0:
        double_turns[key] = int(double_turns[key]) - 1
    engine.state.active_player = 1 - engine.state.active_player
    engine.state.turn_number += 1
    set_phase(engine, "setup")
    refresh_player_flags(engine)
    engine._reset_effect_usage_this_turn()
    engine._reset_turn_once_markers_this_turn()
