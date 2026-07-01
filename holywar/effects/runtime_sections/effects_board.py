from __future__ import annotations

from typing import TYPE_CHECKING

from holywar.effects.runtime import _norm, EffectSpec

if TYPE_CHECKING:
    from holywar.core.engine import GameEngine


class RuntimeEffectsBoardMixin:
    if TYPE_CHECKING:
        def _resolve_player_scope(self, owner_idx: int, scope: str | None) -> int: ...

    def _apply_effect_board_action(self, engine: GameEngine, owner_idx: int, source_uid: str, targets: list[str], effect: EffectSpec, action: str) -> bool:
            if action == "request_end_turn":
                runtime_state = engine.state.flags.setdefault("runtime_state", {})
                runtime_state["request_end_turn"] = True
                return True
            if action == "set_next_turn_draw_override":
                target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
                amount = max(0, int(effect.amount or 0))
                flags = engine.state.flags.setdefault("next_turn_draw_override", {"0": 0, "1": 0})
                flags[str(target)] = amount
                return True
            if action == "set_double_cost_next_turn":
                target = self._resolve_player_scope(owner_idx, effect.target_player or "opponent")
                amount = max(0, int(effect.amount or 1))
                flags = engine.state.flags.setdefault("double_cost_next_turn", {"0": 0, "1": 0})
                key = str(target)
                flags[key] = int(flags.get(key, 0)) + amount
                return True
            if action == "set_no_attacks_until_card_draw":
                runtime_state = engine.state.flags.setdefault("runtime_state", {})
                locked_sources = list(runtime_state.get("no_attacks_until_draw_sources", []) or [])
                if source_uid and source_uid not in locked_sources:
                    locked_sources.append(source_uid)
                runtime_state["no_attacks_until_draw_sources"] = locked_sources
                return True
            if action == "set_no_attacks_this_turn":
                engine.state.flags["no_attacks_turn"] = int(engine.state.turn_number)
                return True
            if action == "swap_attack_defense_rows":
                target = self._resolve_player_scope(owner_idx, effect.target_player or "opponent")
                player = engine.state.players[target]
                player.attack, player.defense = player.defense, player.attack
                return True
            if action == "transfer_target_control_until_turn_end":
                target_controller = self._resolve_player_scope(owner_idx, effect.target_player or "opponent")
                runtime_state = engine.state.flags.setdefault("runtime_state", {})
                pending_returns = list(runtime_state.get("temporary_control_returns", []) or [])
                expire_turn = int(engine.state.turn_number)

                for t_uid in targets:
                    inst = engine.state.instances.get(t_uid)
                    if inst is None:
                        continue
                    if _norm(inst.definition.card_type) not in {"santo", "token"}:
                        continue

                    board_owner = engine._find_board_owner_of_uid(t_uid)
                    if board_owner is None or int(board_owner) == int(target_controller):
                        continue

                    from_player = engine.state.players[board_owner]
                    to_player = engine.state.players[target_controller]

                    from_zone = ""
                    from_slot = -1
                    if t_uid in from_player.attack:
                        from_zone = "attack"
                        from_slot = int(from_player.attack.index(t_uid))
                        from_player.attack[from_slot] = None
                        back_uid = from_player.defense[from_slot]
                        if back_uid is not None and from_player.attack[from_slot] is None:
                            from_player.attack[from_slot] = back_uid
                            from_player.defense[from_slot] = None
                    elif t_uid in from_player.defense:
                        from_zone = "defense"
                        from_slot = int(from_player.defense.index(t_uid))
                        from_player.defense[from_slot] = None
                    else:
                        continue

                    placed = False
                    if from_zone == "attack" and 0 <= from_slot < len(to_player.attack) and to_player.attack[from_slot] is None:
                        to_player.attack[from_slot] = t_uid
                        placed = True
                    elif from_zone == "defense" and 0 <= from_slot < len(to_player.defense) and to_player.defense[from_slot] is None:
                        to_player.defense[from_slot] = t_uid
                        placed = True
                    else:
                        slot = engine._first_open(to_player.attack)
                        if slot is not None:
                            to_player.attack[slot] = t_uid
                            placed = True
                        else:
                            slot = engine._first_open(to_player.defense)
                            if slot is not None:
                                to_player.defense[slot] = t_uid
                                placed = True

                    if not placed:
                        if from_zone == "attack" and 0 <= from_slot < len(from_player.attack) and from_player.attack[from_slot] is None:
                            from_player.attack[from_slot] = t_uid
                        elif from_zone == "defense" and 0 <= from_slot < len(from_player.defense) and from_player.defense[from_slot] is None:
                            from_player.defense[from_slot] = t_uid
                        else:
                            fallback_slot = engine._first_open(from_player.attack)
                            if fallback_slot is not None:
                                from_player.attack[fallback_slot] = t_uid
                            else:
                                fallback_slot = engine._first_open(from_player.defense)
                                if fallback_slot is not None:
                                    from_player.defense[fallback_slot] = t_uid
                        continue

                    if "sin_to_controller_on_death" not in inst.blessed:
                        inst.blessed.append("sin_to_controller_on_death")

                    pending_returns = [rec for rec in pending_returns if str(rec.get("uid", "")) != t_uid]
                    pending_returns.append(
                        {
                            "uid": t_uid,
                            "from_owner": int(board_owner),
                            "to_owner": int(target_controller),
                            "from_zone": from_zone,
                            "from_slot": int(from_slot),
                            "expires_turn": expire_turn,
                        }
                    )

                runtime_state["temporary_control_returns"] = pending_returns
                return True
            if action == "set_attack_shield_this_turn":
                target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
                shield = engine.state.flags.setdefault("attack_shield_turn", {})
                shield[str(target)] = int(engine.state.turn_number)
                return True
            if action == "set_attack_shield_next_opponent_turn":
                target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
                shield = engine.state.flags.setdefault("attack_shield_turn", {})
                shield[str(target)] = int(engine.state.turn_number) + 1
                return True
            if action == "win_the_game":
                winner = self._resolve_player_scope(owner_idx, effect.target_player or "me")
                if engine.state.winner is None:
                    loser = 1 - int(winner)
                    engine.state.players[loser].sin = max(100, int(engine.state.players[loser].sin))
                    engine.state.winner = int(winner)
                    engine.state.log(f"{engine.state.players[winner].name} vince il duello per effetto carta.")
                return True
            if action == "swap_attack_defense":
                player = engine.state.players[owner_idx]
                attack_slot = next((i for i, uid in enumerate(player.attack) if uid is not None), None)
                defense_slot = next((i for i, uid in enumerate(player.defense) if uid is not None), None)
                if attack_slot is None or defense_slot is None:
                    return True
                player.attack[attack_slot], player.defense[defense_slot] = player.defense[defense_slot], player.attack[attack_slot]
                return True
            if action == "swap_selected_attack_defense":
                selected = str(engine.state.flags.get("_runtime_selected_target", "")).strip()
                selected_uids = [uid.strip() for uid in selected.split(",") if uid.strip()]
                if len(selected_uids) < 2:
                    return True

                uid_a = selected_uids[0]
                uid_b = selected_uids[1]
                if uid_a not in engine.state.instances or uid_b not in engine.state.instances:
                    return True

                controller_a = int(engine.state.instances[uid_a].owner)
                controller_b = int(engine.state.instances[uid_b].owner)
                if controller_a != controller_b:
                    return True

                player = engine.state.players[controller_a]
                attack_slot_a = next((i for i, uid in enumerate(player.attack) if uid == uid_a), None)
                defense_slot_a = next((i for i, uid in enumerate(player.defense) if uid == uid_a), None)
                attack_slot_b = next((i for i, uid in enumerate(player.attack) if uid == uid_b), None)
                defense_slot_b = next((i for i, uid in enumerate(player.defense) if uid == uid_b), None)

                uid_in_attack: str | None = None
                uid_in_defense: str | None = None
                attack_slot: int | None = None
                defense_slot: int | None = None

                if attack_slot_a is not None and defense_slot_b is not None:
                    uid_in_attack = uid_a
                    uid_in_defense = uid_b
                    attack_slot = attack_slot_a
                    defense_slot = defense_slot_b
                elif attack_slot_b is not None and defense_slot_a is not None:
                    uid_in_attack = uid_b
                    uid_in_defense = uid_a
                    attack_slot = attack_slot_b
                    defense_slot = defense_slot_a

                if uid_in_attack is None or uid_in_defense is None or attack_slot is None or defense_slot is None:
                    return True

                player.attack[attack_slot] = uid_in_defense
                player.defense[defense_slot] = uid_in_attack
                return True
            if action == "increase_faith_per_opponent_saints":
                target_bonus = max(0, int(effect.amount))
                count = len(engine.all_saints_on_field(1 - owner_idx))
                for t_uid in targets:
                    inst = engine.state.instances[t_uid]
                    inst.current_faith = (inst.current_faith or 0) + (count * target_bonus)
                return True
            if action == "increase_faith_if_damaged":
                amount = max(0, int(effect.amount))
                for t_uid in targets:
                    inst = engine.state.instances[t_uid]
                    base_faith = inst.definition.faith or 0
                    current_faith = inst.current_faith if inst.current_faith is not None else base_faith
                    if current_faith < base_faith:
                        inst.current_faith = current_faith + amount
                return True
            return False
