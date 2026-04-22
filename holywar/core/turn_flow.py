from __future__ import annotations

import unicodedata
from typing import TYPE_CHECKING

from holywar.core.state import TURN_INSPIRATION, hand_has_space_for_non_innata, is_innata_card_type
from holywar.effects.runtime import EffectSpec, runtime_cards
from holywar.effects.state_flags import ensure_runtime_state, refresh_player_flags, set_phase

if TYPE_CHECKING:
    from holywar.core.engine import GameEngine


def _norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", text)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


def _emit_end_turn_events(engine: "GameEngine", current: int) -> None:
    engine._emit_event("on_main_phase_end", current, player=current)
    engine._emit_event("on_turn_end", current, player=current)
    engine._emit_event("on_my_turn_end", current, player=current)
    engine._emit_event("on_opponent_turn_end", 1 - current, opponent=current)


# Performs the initial setup draw for both players at match start.
def initial_setup_draw(engine: "GameEngine") -> None:
    for idx in (0, 1):
        draw_cards(engine, idx, 5)
        pending = list(
            engine.state.flags.setdefault("innate_pending_setup", {"0": [], "1": []}).get(str(idx), []) or []
        )
        player = engine.state.players[idx]
        for uid in pending:
            if uid not in engine.state.instances:
                continue
            for pool_name in ("deck", "white_deck", "graveyard", "excommunicated"):
                pool = getattr(player, pool_name)
                if uid in pool:
                    pool.remove(uid)
            if uid not in player.hand:
                player.hand.append(uid)
        engine.state.flags.setdefault("innate_pending_setup", {"0": [], "1": []})[str(idx)] = []
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
        if not hand_has_space_for_non_innata(player, engine.state.instances):
            break
        if not player.deck:
            break
        drawn_uid = player.deck.pop()
        player.hand.append(drawn_uid)
        drawn += 1
        engine.state.flags.setdefault("cards_drawn_this_turn", {"0": [], "1": []}).setdefault(str(player_idx), []).append(drawn_uid)
        engine._emit_event("on_card_drawn", player_idx, card=drawn_uid, from_zone="relicario")
        card_name = engine.state.instances[drawn_uid].definition.name

        if _norm(card_name) == _norm("Albero Sacro"):
            engine.state.log(
                f"auto_play={runtime_cards.get_auto_play_on_draw(card_name)} "
                f"end_turn_on_draw={runtime_cards.get_end_turn_on_draw(card_name)} "
                f"mano_size={len(player.hand)} deck_size={len(player.deck)}"
            )

        if runtime_cards.get_auto_play_on_draw(card_name):
            flags = engine.state.flags
            previous_source = flags.get("_runtime_source_card")
            previous_selected = flags.get("_runtime_selected_target")

            if _norm(card_name) == _norm("Albero Sacro"):
                engine.state.log(
                    f"in_hand={drawn_uid in player.hand}"
                )

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

            if _norm(card_name) == _norm("Albero Sacro"):
                zone_now = engine._locate_uid_zone(player_idx, drawn_uid)
                engine.state.log(
                    f"in_hand={drawn_uid in player.hand}"
                )

        if runtime_cards.get_end_turn_on_draw(card_name):
            runtime_state = engine.state.flags.setdefault("runtime_state", {})
            current_phase = str(engine.state.phase).strip().lower()
            is_preparation_draw = current_phase == "preparation"
            is_real_turn_draw = (
                int(player_idx) == int(engine.state.active_player)
                and current_phase in {"draw", "main", "active", "turn_start"}
            )

            if _norm(card_name) == _norm("Albero Sacro"):
                engine.state.log(
                    f"is_preparation_draw={is_preparation_draw} "
                    f"is_real_turn_draw={is_real_turn_draw} "
                    f"active_player={engine.state.active_player} phase={engine.state.phase}"
                )

            if is_preparation_draw:
                pending = runtime_state.setdefault("preparation_end_turn_pending", [])
                if player_idx not in pending:
                    pending.append(player_idx)

                prep_auto_end = runtime_state.setdefault("request_end_preparation_players", [])
                if player_idx not in prep_auto_end:
                    prep_auto_end.append(player_idx)

            elif is_real_turn_draw:
                runtime_state["request_end_turn_player"] = player_idx

        engine._emit_event("after_card_drawn_from_deck", player_idx, card=drawn_uid)
        engine._emit_event("on_opponent_draws", 1 - player_idx, card=drawn_uid, opponent=player_idx)
    refresh_player_flags(engine)
    return drawn


def _remove_unplayed_innate_cards(engine: "GameEngine", player_idx: int) -> None:
    player = engine.state.players[player_idx]
    active = set(engine.state.flags.setdefault("innate_active_uids", {"0": [], "1": []}).get(str(player_idx), []) or [])
    removed = engine.state.flags.setdefault("innate_removed_uids", {"0": [], "1": []}).setdefault(str(player_idx), [])
    for uid, inst in engine.state.instances.items():
        if int(inst.owner) != int(player_idx):
            continue
        if not is_innata_card_type(inst.definition.card_type):
            continue
        if uid in active:
            continue
        removed_any = False
        for pool_name in ("hand", "deck", "white_deck", "graveyard", "excommunicated"):
            pool = getattr(player, pool_name)
            if uid in pool:
                pool.remove(uid)
                removed_any = True
        for zone in (player.attack, player.defense, player.artifacts):
            for i, z_uid in enumerate(zone):
                if z_uid == uid:
                    zone[i] = None
                    removed_any = True
        if player.building == uid:
            player.building = None
            removed_any = True
        if removed_any and uid not in removed:
            removed.append(uid)
            engine.state.log(f"{player.name}: {inst.definition.name} (Innata) non giocata in preparazione e stata eliminata.")


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
            if engine.place_card_from_uid(current, token_uid, "defense", i):
                final_zone = engine._locate_uid_zone(current, token_uid)
                if final_zone == "defense":
                    engine.state.log(f"{player.name} evoca {token_name} dietro {engine.state.instances[a_uid].definition.name}.")
                else:
                    engine.state.log(f"{player.name} evoca {token_name} in attacco.")


# Resolves the active player's draw phase, including special draw modifiers.
def _run_draw_phase(engine: "GameEngine", current: int) -> int:
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

    bonus_draw = runtime_cards.get_context_bonus_amount(
        engine,
        engine.state.active_player,
        context="turn_draw",
        amount_mode="flat",
    )
    return draw_cards(engine, engine.state.active_player, 3 + bonus_draw)


# Starts the active player's turn and advances the game into the main phase when appropriate.
def start_turn(engine: "GameEngine") -> None:
    current = engine.state.active_player
    player = engine.state.players[current]
    runtime_state = ensure_runtime_state(engine)
    runtime_state["battle_phase_started"] = False
    stale_player = runtime_state.get("request_end_turn_player", None)
    if stale_player is not None and stale_player not in {0, 1}:
        runtime_state.pop("request_end_turn_player", None)

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
        prep_auto_end = runtime_state.setdefault("request_end_preparation_players", [])

        if current in prep_auto_end:
            prep_auto_end.remove(current)
            engine.state.log(f"{player.name} termina immediatamente la preparazione.")
            end_turn(engine)
            return

        engine.state.log(
            f"Preparazione: {player.name} dispone di 10 Ispirazione e non puo attaccare."
        )
        return

    drawn = _run_draw_phase(engine, current)
    engine._emit_event("on_draw_phase_end", current, player=current, drawn=drawn)

    debug_request_end_turn_player = runtime_state.get("request_end_turn_player", None)
    engine.state.log(
        f"request_end_turn_player={debug_request_end_turn_player} "
        f"active_player={engine.state.active_player} phase={engine.state.phase}"
    )

    if runtime_state.get("request_end_turn_player", None) == current:
        runtime_state.pop("request_end_turn_player", None)
        engine.state.log(f"{player.name} termina immediatamente il turno.")
        end_turn(engine)
        return

    set_phase(engine, "main")
    engine._emit_event("on_main_phase_start", current, player=current)
    engine.state.log(f"Turno {engine.state.turn_number}: {player.name} pesca {drawn} carte e ottiene 10 Ispirazione.")
    refresh_player_flags(engine)


# Completes end-of-turn effects and hands control to the next player or phase.
def end_turn(engine: "GameEngine") -> None:
    current = engine.state.active_player
    runtime_state = ensure_runtime_state(engine)
    was_preparation = str(engine.state.phase).strip().lower() == "preparation"

    engine.state.log(
        f"player={engine.state.players[current].name} "
        f"phase_before={engine.state.phase} turn={engine.state.turn_number}"
    )

    if bool(runtime_state.get("battle_phase_started", False)):
        set_phase(engine, "battle")
        engine._emit_event("on_battle_phase_end", current, player=current)
        runtime_state["battle_phase_started"] = False

    set_phase(engine, "end")

    if not was_preparation:
        _emit_end_turn_events(engine, current)

    engine.state.flags.setdefault("cards_drawn_this_turn", {"0": [], "1": []})[str(current)] = []
    engine._cleanup_zero_faith_saints()
    engine.check_win_conditions()
    if engine.state.winner is not None:
        return

    if was_preparation:
        _remove_unplayed_innate_cards(engine, current)
        engine.state.preparation_turns_done += 1

        pending = runtime_state.setdefault("preparation_end_turn_pending", [])
        if current not in pending:
            pending.append(current)

        if engine.state.preparation_turns_done >= 2:
            runtime_state.pop("preparation_end_turn_pending", None)

            engine._emit_event("on_preparation_complete", current, player=current)

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