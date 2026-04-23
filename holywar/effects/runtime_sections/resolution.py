from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable
import json
from pathlib import Path

from holywar.core import state
from holywar.core.state import MAX_HAND, CardInstance
from holywar.effects.card_scripts_loader import iter_card_scripts
from holywar.scripting_api import RuleEventContext
from holywar.data.importer import load_cards_json
from holywar.data.models import CardDefinition
from holywar.effects.runtime import (
    _norm,
    _card_name_haystack,
    _card_name_variants,
    _card_matches_name,
    SUPPORTED_EFFECT_ACTIONS,
    EFFECT_ACTION_ALIASES,
    SUPPORTED_CONDITION_KEYS,
    TriggerSpec,
    CardFilterSpec,
    TargetSpec,
    EffectSpec,
    TriggeredEffectSpec,
    ActionSpec,
    CardScript,
)

if TYPE_CHECKING:
    from holywar.core.engine import GameEngine


class RuntimeResolutionMixin:
    """Play/enter/activate resolution and trigger binding lifecycle."""

    def can_play(
        self,
        engine: GameEngine,
        player_idx: int,
        uid: str,
        target: str | None = None,
    ) -> tuple[bool, str | None]:
        self.ensure_all_cards_migrated(engine)
        inst = engine.state.instances[uid]
        script = self._scripts.get(_norm(inst.definition.name), CardScript(name=inst.definition.name))
        if not script.can_play_from_hand:
            return (False, "Questa carta non puo essere giocata dalla mano.")

        if script.play_requirements:
            ok = self._eval_condition_node(
                RuleEventContext(engine=engine, event="can_play", player_idx=player_idx, payload={"card": uid}),
                player_idx,
                script.play_requirements,
            )
            if not ok:
                return (False, "Non puoi giocare questa carta nelle condizioni attuali.")

        if script.on_play_actions:
            return self._validate_manual_target_actions(
                engine=engine,
                owner_idx=player_idx,
                source_uid=uid,
                actions=script.on_play_actions,
                selected_target=target,
                event_name="on_play",
                empty_pool_message="Nessun bersaglio valido disponibile per questa carta.",
                missing_selection_message="Devi selezionare almeno un bersaglio valido per giocare questa carta.",
            )
        return (True, None)

    def can_activate(
        self,
        engine: GameEngine,
        player_idx: int,
        uid: str,
        target: str | None = None,
    ) -> tuple[bool, str | None]:
        self.ensure_all_cards_migrated(engine)
        inst = engine.state.instances[uid]
        script = self._scripts.get(_norm(inst.definition.name), CardScript(name=inst.definition.name))

        mode = _norm(script.on_activate_mode)

        # Nessuna abilità attivabile manualmente
        if mode not in {"scripted", "custom"}:
            return (False, "Questa carta non ha un effetto attivabile.")

        if not script.on_activate_actions:
            return (False, "Questa carta non ha un effetto attivabile.")

        return self._validate_manual_target_actions(
            engine=engine,
            owner_idx=player_idx,
            source_uid=uid,
            actions=script.on_activate_actions,
            selected_target=target,
            event_name="on_activate",
            empty_pool_message="Nessun bersaglio valido disponibile per questa abilita.",
            missing_selection_message="Devi selezionare almeno un bersaglio valido per attivare questa abilita.",
        )

    def resolve_play(self, engine: GameEngine, player_idx: int, uid: str, target: str | None) -> object:
        self.ensure_all_cards_migrated(engine)
        inst = engine.state.instances[uid]
        script = self._scripts.get(_norm(inst.definition.name), CardScript(name=inst.definition.name))
        mode = _norm(script.on_play_mode)
        flags = engine.state.flags
        previous_source = flags.get("_runtime_effect_source")

        flags["_runtime_effect_source"] = uid
        flags["_runtime_source_card"] = uid
        flags["_runtime_selected_target"] = str(target or "")
        try:
            is_saint = _norm(inst.definition.card_type) in {"santo", "token"}
            if mode in {"noop", "none"}:
                return f"{inst.definition.name}: nessun effetto all'ingresso."
            if mode in {"scripted", "custom"} and script.on_play_actions:
                self._run_play_actions(engine, player_idx, uid, script.on_play_actions)
                return f"{inst.definition.name}: effetto risolto via script."
            if mode == "auto" and script.on_play_actions:
                self._run_play_actions(engine, player_idx, uid, script.on_play_actions)
                return f"{inst.definition.name}: effetto risolto via script."
            if mode in {"scripted", "custom", "auto"} and not script.on_play_actions:
                return f"{inst.definition.name}: nessun effetto scriptato."
            if is_saint:
                return f"{inst.definition.name}: nessun effetto scriptato."
            return self._legacy_removed_message(engine, inst.definition.name, "on_play", mode)
        finally:
            if previous_source is None:
                flags.pop("_runtime_effect_source", None)
            else:
                flags["_runtime_effect_source"] = previous_source

            if not flags.get("_runtime_waiting_for_reveal"):
                flags.pop("_runtime_source_card", None)
                flags.pop("_runtime_selected_target", None)
                flags.pop("_runtime_action_index", None)

    def _run_play_actions(
        self,
        engine: GameEngine,
        owner_idx: int,
        source_uid: str,
        actions: list[ActionSpec],
        start_index: int = 0,
    ) -> None:
        flags = engine.state.flags
        flags["_runtime_pending_mode"] = "play"

        for i in range(start_index, len(actions)):
            if flags.get("_runtime_waiting_for_reveal"):
                flags["_runtime_action_index_resume"] = str(i)
                flags["_runtime_resume_source"] = source_uid
                flags["_runtime_resume_owner"] = str(owner_idx)
                break

            action = actions[i]
            flags["_runtime_action_index"] = str(i)

            if action.condition and not self._eval_condition_node(
                RuleEventContext(engine=engine, event="on_play", player_idx=owner_idx, payload={"card": source_uid}),
                owner_idx,
                action.condition,
            ):
                continue

            targets = self._resolve_targets(engine, owner_idx, action.target)
            self._apply_effect(engine, owner_idx, source_uid, targets, action.effect)

            if flags.get("_runtime_waiting_for_reveal"):
                if bool(flags.pop("_runtime_resume_same_action", False)):
                    flags["_runtime_action_index_resume"] = str(i)
                else:
                    flags["_runtime_action_index_resume"] = str(i + 1)
                flags["_runtime_resume_source"] = source_uid
                flags["_runtime_resume_owner"] = str(owner_idx)
                break

        flags.pop("_runtime_action_index", None)
        if not flags.get("_runtime_waiting_for_reveal"):
            flags.pop("_runtime_pending_mode", None)

    def resolve_enter(self, engine: GameEngine, player_idx: int, uid: str) -> object:
        self.ensure_all_cards_migrated(engine)
        self.on_enter_bind_triggers(engine, player_idx, uid)
        inst = engine.state.instances[uid]
        script = self._scripts.get(_norm(inst.definition.name), CardScript(name=inst.definition.name))
        mode = _norm(script.on_enter_mode)
        flags = engine.state.flags
        previous_source = flags.get("_runtime_effect_source")
        flags["_runtime_effect_source"] = uid
        flags["_runtime_source_card"] = uid
        flags["_runtime_selected_target"] = ""

        try:
            is_saint = _norm(inst.definition.card_type) in {"santo", "token"}
            if mode in {"noop", "none"}:
                return None
            if mode in {"scripted", "custom"} and script.on_enter_actions:
                self._run_enter_actions(engine, player_idx, uid, script.on_enter_actions)
                return f"{inst.definition.name}: effetto di ingresso risolto via script."
            if mode == "auto" and script.on_enter_actions:
                self._run_enter_actions(engine, player_idx, uid, script.on_enter_actions)
                return f"{inst.definition.name}: effetto di ingresso risolto via script."
            if mode in {"scripted", "custom", "auto"} and not script.on_enter_actions:
                return None
            if is_saint:
                return None
            return self._legacy_removed_message(engine, inst.definition.name, "on_enter", mode)
        finally:
            if previous_source is None:
                flags.pop("_runtime_effect_source", None)
            else:
                flags["_runtime_effect_source"] = previous_source
            if not flags.get("_runtime_waiting_for_reveal"):
                flags.pop("_runtime_source_card", None)
                flags.pop("_runtime_selected_target", None)

    def resolve_activate(self, engine: GameEngine, player_idx: int, uid: str, target: str | None) -> object:
        self.ensure_all_cards_migrated(engine)
        inst = engine.state.instances[uid]
        script = self._scripts.get(_norm(inst.definition.name), CardScript(name=inst.definition.name))
        mode = _norm(script.on_activate_mode)
        flags = engine.state.flags
        previous_source = flags.get("_runtime_effect_source")

        flags["_runtime_effect_source"] = uid
        flags["_runtime_source_card"] = uid
        flags["_runtime_selected_target"] = str(target or "")
        try:
            is_saint = _norm(inst.definition.card_type) in {"santo", "token"}
            if mode in {"scripted", "custom"} and script.on_activate_actions:
                self._run_activate_actions(engine, player_idx, uid, script.on_activate_actions)
                if script.activate_once_per_turn and not flags.get("_runtime_waiting_for_reveal"):
                    engine.mark_activated_this_turn(uid)
                return f"{inst.definition.name}: effetto attivato via script."
            if mode in {"scripted", "custom"} and not script.on_activate_actions:
                return f"{inst.definition.name}: nessun effetto attivabile."
            if mode in {"auto", "noop", "none"}:
                return f"{inst.definition.name}: nessun effetto attivabile."
            if is_saint:
                return f"{inst.definition.name}: nessun effetto scriptato."
            return self._legacy_removed_message(engine, inst.definition.name, "on_activate", mode)
        finally:
            if previous_source is None:
                flags.pop("_runtime_effect_source", None)
            else:
                flags["_runtime_effect_source"] = previous_source
            flags.pop("_runtime_source_card", None)
            flags.pop("_runtime_selected_target", None)
            flags.pop("_runtime_selected_option", None)

    def _legacy_removed_message(self, engine: GameEngine, card_name: str, event: str, mode: str) -> str:
        _ = engine
        _ = event
        _ = mode
        return f"{card_name}: nessun effetto scriptato."

    def _run_activate_actions(
        self,
        engine: GameEngine,
        owner_idx: int,
        source_uid: str,
        actions: list[ActionSpec],
        start_index: int = 0,
    ) -> None:
        flags = engine.state.flags
        flags["_runtime_pending_mode"] = "activate"
        for i in range(start_index, len(actions)):
            if flags.get("_runtime_waiting_for_reveal"):
                flags["_runtime_action_index_resume"] = str(i)
                flags["_runtime_resume_source"] = source_uid
                flags["_runtime_resume_owner"] = str(owner_idx)
                break
            action = actions[i]
            if action.condition and not self._eval_condition_node(
                RuleEventContext(engine=engine, event="on_activate", player_idx=owner_idx, payload={"card": source_uid}),
                owner_idx,
                action.condition,
            ):
                continue
            targets = self._resolve_targets(engine, owner_idx, action.target)
            self._apply_effect(engine, owner_idx, source_uid, targets, action.effect)
            if flags.get("_runtime_waiting_for_reveal"):
                if bool(flags.pop("_runtime_resume_same_action", False)):
                    flags["_runtime_action_index_resume"] = str(i)
                else:
                    flags["_runtime_action_index_resume"] = str(i + 1)
                flags["_runtime_resume_source"] = source_uid
                flags["_runtime_resume_owner"] = str(owner_idx)
                break

        if not flags.get("_runtime_waiting_for_reveal"):
            flags.pop("_runtime_pending_mode", None)

    def resume_pending_effect(self, engine: GameEngine) -> None:
        flags = engine.state.flags
        source_uid = str(flags.get("_runtime_resume_source", "")).strip()
        owner_idx_raw = flags.get("_runtime_resume_owner")
        if not source_uid or owner_idx_raw is None:
            return

        inst = engine.state.instances.get(source_uid)
        if inst is None:
            flags.pop("_runtime_resume_source", None)
            flags.pop("_runtime_resume_owner", None)
            flags.pop("_runtime_action_index_resume", None)
            flags.pop("_runtime_pending_mode", None)
            return

        owner_idx = int(owner_idx_raw)
        script = self._scripts.get(_norm(inst.definition.name), CardScript(name=inst.definition.name))
        start_index = int(flags.get("_runtime_action_index_resume", 0))
        mode = str(flags.get("_runtime_pending_mode", "")).strip().lower()
        previous_source = flags.get("_runtime_effect_source")

        flags["_runtime_effect_source"] = source_uid
        flags["_runtime_source_card"] = source_uid
        try:
            if mode == "play":
                self._run_play_actions(engine, owner_idx, source_uid, script.on_play_actions, start_index=start_index)
            elif mode == "enter":
                self._run_enter_actions(engine, owner_idx, source_uid, script.on_enter_actions, start_index=start_index)
            elif mode == "activate":
                self._run_activate_actions(engine, owner_idx, source_uid, script.on_activate_actions, start_index=start_index)
            elif mode == "trigger_action":
                action_name = str(flags.get("_runtime_trigger_action", "")).strip()
                target_player = str(flags.get("_runtime_trigger_target_player", "me")).strip() or "me"
                trigger_card_name = str(flags.get("_runtime_trigger_card_name", "")).strip() or None
                if action_name:
                    self._apply_effect(
                        engine,
                        owner_idx,
                        source_uid,
                        [],
                        EffectSpec(action=action_name, target_player=target_player, card_name=trigger_card_name),
                    )
        finally:
            if previous_source is None:
                flags.pop("_runtime_effect_source", None)
            else:
                flags["_runtime_effect_source"] = previous_source

            if not flags.get("_runtime_waiting_for_reveal"):
                if mode == "activate" and script.activate_once_per_turn:
                    engine.mark_activated_this_turn(source_uid)
                flags.pop("_runtime_source_card", None)
                flags.pop("_runtime_selected_option", None)
                flags.pop("_runtime_resume_source", None)
                flags.pop("_runtime_resume_owner", None)
                flags.pop("_runtime_action_index_resume", None)
                flags.pop("_runtime_pending_mode", None)
                flags.pop("_runtime_trigger_action", None)
                flags.pop("_runtime_trigger_target_player", None)
                flags.pop("_runtime_trigger_card_name", None)

    def _run_enter_actions(
        self,
        engine: GameEngine,
        owner_idx: int,
        source_uid: str,
        actions: list[ActionSpec],
        start_index: int = 0,
    ) -> None:
        flags = engine.state.flags
        flags["_runtime_pending_mode"] = "enter"
        for i in range(start_index, len(actions)):
            if flags.get("_runtime_waiting_for_reveal"):
                flags["_runtime_action_index_resume"] = str(i)
                flags["_runtime_resume_source"] = source_uid
                flags["_runtime_resume_owner"] = str(owner_idx)
                break
            action = actions[i]
            flags["_runtime_action_index"] = str(i)
            if action.condition and not self._eval_condition_node(
                RuleEventContext(engine=engine, event="on_enter", player_idx=owner_idx, payload={"card": source_uid}),
                owner_idx,
                action.condition,
            ):
                continue
            targets = self._resolve_targets(engine, owner_idx, action.target)
            self._apply_effect(engine, owner_idx, source_uid, targets, action.effect)
            if flags.get("_runtime_waiting_for_reveal"):
                if bool(flags.pop("_runtime_resume_same_action", False)):
                    flags["_runtime_action_index_resume"] = str(i)
                else:
                    flags["_runtime_action_index_resume"] = str(i + 1)
                flags["_runtime_resume_source"] = source_uid
                flags["_runtime_resume_owner"] = str(owner_idx)
                break
        flags.pop("_runtime_action_index", None)
        if not flags.get("_runtime_waiting_for_reveal"):
            flags.pop("_runtime_pending_mode", None)

    def on_enter_bind_triggers(self, engine: GameEngine, owner_idx: int, source_uid: str) -> None:
        self.ensure_all_cards_migrated(engine)
        script = self._scripts.get(_norm(engine.state.instances[source_uid].definition.name))
        if not script or not script.triggered_effects:
            return
        eng_key = id(engine)
        by_source = self._bindings.setdefault(eng_key, {})
        previous_bindings = by_source.pop(source_uid, [])
        if previous_bindings:
            api = engine.rules_api(owner_idx)
            for event_name, handler in previous_bindings:
                try:
                    api.unsubscribe(event_name, handler)
                except Exception:
                    pass
        by_source[source_uid] = []

        api = engine.rules_api(owner_idx)

        for te in script.triggered_effects:
            event_name = te.trigger.event
            allow_source_off_field = {
                "on_this_card_destroyed",
                "on_card_destroyed_on_field",
                "on_saint_destroyed_by_effect",
                "on_saint_defeated_in_battle",
                "on_saint_defeated_or_destroyed",
                "on_card_drawn",
                "on_this_card_leaves_field",
                "on_card_sent_to_graveyard",
                "on_card_excommunicated",
                "on_card_returned_to_reliquario",
                "on_card_shuffled_into_reliquario",
            }

            def _handler(ctx: RuleEventContext, _te=te, _owner=owner_idx, _source=source_uid, _event_name=event_name):
                if _event_name not in allow_source_off_field and not self._is_uid_on_field(ctx.engine, _source):
                    return
                if _te.trigger.event in {"on_my_turn_start", "on_my_turn_end"} and ctx.player_idx != _owner:
                    return
                if _te.trigger.event in {"on_opponent_turn_start", "on_opponent_turn_end"} and ctx.player_idx != _owner:
                    return
                if _te.trigger.event.startswith("on_this_card_"):
                    event_uid = str(ctx.payload.get("card", ctx.payload.get("saint", ctx.payload.get("token", ""))))
                    if event_uid != _source:
                        return
                if _te.trigger.event == "on_opponent_saint_enters_field":
                    saint_uid = str(ctx.payload.get("saint", ctx.payload.get("card", ""))).strip()
                    source_inst = ctx.engine.state.instances.get(_source)
                    saint_inst = ctx.engine.state.instances.get(saint_uid)
                    if source_inst is None or saint_inst is None:
                        return
                    if int(saint_inst.owner) == int(source_inst.owner):
                        return
                if not self._event_matches(ctx, _owner, _te.trigger.condition):
                    return
                source_inst = ctx.engine.state.instances.get(_source)
                source_name = source_inst.definition.name if source_inst is not None else _source
                event_card_uid = str(ctx.payload.get("card", ctx.payload.get("saint", ctx.payload.get("token", ""))))
                event_card_name = (
                    ctx.engine.state.instances[event_card_uid].definition.name
                    if event_card_uid in ctx.engine.state.instances
                    else event_card_uid
                )
                ctx.engine.state.log(f"{source_name}: trigger {ctx.event} su {event_card_name} (turno {ctx.engine.state.turn_number}).")
                ctx.engine.state.flags["_runtime_event_card"] = str(
                    ctx.payload.get("card", ctx.payload.get("saint", ctx.payload.get("token", "")))
                )
                ctx.engine.state.flags["_runtime_event_source"] = str(ctx.payload.get("source", ""))
                ctx.engine.state.flags["_runtime_event_name"] = str(ctx.event)
                ctx.engine.state.flags["_runtime_source_card"] = _source
                try:
                    targets = self._resolve_targets(ctx.engine, _owner, _te.target)
                    if not targets:
                        self._apply_effect(ctx.engine, _owner, _source, [], _te.effect)
                        return
                    self._apply_effect(ctx.engine, _owner, _source, targets, _te.effect)
                finally:
                    ctx.engine.state.flags.pop("_runtime_event_card", None)
                    ctx.engine.state.flags.pop("_runtime_event_source", None)
                    ctx.engine.state.flags.pop("_runtime_event_name", None)
                    ctx.engine.state.flags.pop("_runtime_source_card", None)

            api.subscribe(event_name, _handler)
            by_source[source_uid].append((event_name, _handler))

    def on_leave_unbind_triggers(self, engine: GameEngine, owner_idx: int, source_uid: str) -> None:
        eng_key = id(engine)
        by_source = self._bindings.get(eng_key, {})
        bindings = by_source.pop(source_uid, [])
        if not bindings:
            return

        api = engine.rules_api(owner_idx)
        for event_name, handler in bindings:
            try:
                api.unsubscribe(event_name, handler)
            except Exception:
                pass

    def _ensure_leave_subscription(self, engine: GameEngine) -> None:
        key = id(engine)
        if key in self._subscribed_engines:
            return
        self._subscribed_engines.add(key)
        engine.rules_api(0).subscribe("on_this_card_leaves_field", self._on_source_leaves_field)

    def _on_source_leaves_field(self, ctx: RuleEventContext) -> None:
        source_uid = str(ctx.payload.get("card", ""))
        owner_idx = -1
        inst = ctx.engine.state.instances.get(source_uid)
        if inst is not None:
            owner_idx = inst.owner

        if owner_idx in (0, 1):
            self.on_leave_unbind_triggers(ctx.engine, owner_idx, source_uid)
            if not source_uid:
                    return

        owner_idx = -1
        inst = ctx.engine.state.instances.get(source_uid)
        if inst is not None:
            owner_idx = inst.owner

        if owner_idx in (0, 1):
            self.on_leave_unbind_triggers(ctx.engine, owner_idx, source_uid)

        eng_key = id(ctx.engine)
        source_buffs = self._temp_faith.get(eng_key, {}).pop(source_uid, [])
        for target_uid, amount, marker in source_buffs:
            if target_uid not in ctx.engine.state.instances:
                continue
            inst = ctx.engine.state.instances[target_uid]
            if marker in inst.blessed:
                inst.blessed.remove(marker)
            inst.current_faith = max(0, (inst.current_faith or 0) - amount)

    def _is_uid_on_field(self, engine: GameEngine, uid: str) -> bool:
        for idx in (0, 1):
            p = engine.state.players[idx]
            if uid in (p.attack + p.defense + p.artifacts) or p.building == uid:
                return True
        return False

    def _selected_target_raw_for_current_action(self, engine: GameEngine) -> str:
        raw = str(engine.state.flags.get("_runtime_selected_target", "")).strip()
        if not raw.startswith("seq:"):
            return raw

        action_idx = str(engine.state.flags.get("_runtime_action_index", "")).strip()
        if not action_idx:
            return ""

        body = raw[len("seq:"):]
        for chunk in body.split(";;"):
            if "=" not in chunk:
                continue
            idx, value = chunk.split("=", 1)
            if idx.strip() == action_idx:
                return value.strip()
        return ""

    def _selected_target_uid_for_current_action(self, engine: GameEngine, owner_idx: int) -> str | None:
        raw_selected = self._selected_target_raw_for_current_action(engine)
        if not raw_selected:
            return None
        selected = raw_selected.split(",", 1)[0].strip()
        if selected.startswith("buff:"):
            selected = selected.split(":", 1)[1]
        if selected in engine.state.instances:
            return selected
        if ":" in selected:
            zone, name = selected.split(":", 1)
            zone = _norm(zone)
            name = name.strip()
            if zone in {"deck", "relicario"}:
                player = engine.state.players[owner_idx]
                for uid in player.deck:
                    if _norm(engine.state.instances[uid].definition.name) == _norm(name):
                        return uid
        zone, slot = engine._parse_zone_target(selected)
        if zone is None:
            return None
        player = engine.state.players[owner_idx]
        if zone == "attack" and 0 <= slot < len(player.attack):
            return player.attack[slot]
        if zone == "defense" and 0 <= slot < len(player.defense):
            return player.defense[slot]
        return None

    def _required_min_targets_for_manual_target(self, target: TargetSpec) -> int:
        configured = int(target.min_targets) if target.min_targets is not None else 1
        return max(0, configured)

    def _target_requires_manual_selection(self, target: TargetSpec) -> bool:
        ttype = _norm(target.type)
        if ttype not in {"selected_target", "selected_targets"}:
            return False
        has_explicit_zone = bool(target.zones) or _norm(target.zone) != "field"
        has_filter = bool(
            target.card_filter.name_in
            or (target.card_filter.name_equals or "").strip()
            or (target.card_filter.name_contains or "").strip()
            or (target.card_filter.name_not_contains or "").strip()
            or target.card_filter.card_type_in
            or target.card_filter.exclude_event_card
            or target.card_filter.exclude_buildings_if_my_building_zone_occupied
            or target.card_filter.crosses_gte is not None
            or target.card_filter.crosses_lte is not None
            or target.card_filter.strength_gte is not None
            or target.card_filter.strength_lte is not None
            or target.card_filter.drawn_this_turn_only
            or target.card_filter.top_n_from_zone is not None
        )
        has_limits = (
            target.min_targets is not None
            or target.max_targets is not None
            or target.max_targets_from is not None
        )
        owner_key = _norm(target.owner or "me")
        has_non_default_owner = owner_key not in {"", "me", "owner", "controller"}
        return has_explicit_zone or has_filter or has_limits or has_non_default_owner

    def _collect_selectable_targets_for_manual_target(
        self,
        engine: GameEngine,
        owner_idx: int,
        target: TargetSpec,
    ) -> list[str]:
        zones = [z for z in target.zones if str(z).strip()]
        if not zones:
            zones = [target.zone]

        pool: list[str] = []
        for scoped_owner in self._target_owner_indices(owner_idx, target.owner):
            for zone_name in zones:
                pool.extend(self._get_zone_cards(engine, scoped_owner, zone_name))
        # Preserve order but avoid duplicates.
        deduped_pool = list(dict.fromkeys(pool))
        return self._filter_target_pool(engine, owner_idx, target, deduped_pool)

    def _filter_target_pool(
        self,
        engine: GameEngine,
        owner_idx: int,
        target: TargetSpec,
        pool: list[str],
    ) -> list[str]:
        needle_in = {_norm(v) for v in target.card_filter.name_in}
        needle = _norm(target.card_filter.name_contains or "")
        type_filter = {_norm(v) for v in target.card_filter.card_type_in}
        event_uid = str(engine.state.flags.get("_runtime_event_card", ""))
        source_uid = str(engine.state.flags.get("_runtime_source_card", ""))
        top_n = target.card_filter.top_n_from_zone
        top_n_allowed: set[str] | None = None
        if top_n is not None and int(top_n) > 0:
            top_n_allowed = set(pool[-int(top_n):])
        out: list[str] = []
        for uid in pool:
            if uid not in engine.state.instances:
                continue
            if top_n_allowed is not None and uid not in top_n_allowed:
                continue
            if target.card_filter.exclude_event_card:
                if event_uid and uid == event_uid:
                    continue
                if not event_uid and source_uid and uid == source_uid:
                    continue
            inst = engine.state.instances[uid]
            needle_eq = _norm(target.card_filter.name_equals or "")
            name_variants = _card_name_variants(inst.definition)
            name_haystack = _card_name_haystack(inst.definition)
            if needle_eq and needle_eq not in name_variants:
                continue
            if needle_in and needle_in.isdisjoint(name_variants):
                continue
            if needle and needle not in name_haystack:
                continue
            needle_not = _norm(target.card_filter.name_not_contains or "")
            if needle_not and needle_not in name_haystack:
                continue
            if type_filter and _norm(inst.definition.card_type) not in type_filter:
                continue
            if (
                target.card_filter.exclude_buildings_if_my_building_zone_occupied
                and engine.state.players[owner_idx].building is not None
                and _norm(inst.definition.card_type) == _norm("edificio")
            ):
                continue
            cross_txt = _norm(str(inst.definition.crosses or ""))
            if cross_txt in {"white", "croce bianca"}:
                cross_val = 11
            else:
                try:
                    cross_val = int(float(cross_txt)) if cross_txt else None
                except ValueError:
                    cross_val = None
            if target.card_filter.crosses_gte is not None:
                if cross_val is None or cross_val < int(target.card_filter.crosses_gte):
                    continue
            if target.card_filter.crosses_lte is not None:
                if cross_val is None or cross_val > int(target.card_filter.crosses_lte):
                    continue
            if target.card_filter.strength_gte is not None:
                if int(engine.get_effective_strength(uid)) < int(target.card_filter.strength_gte):
                    continue
            if target.card_filter.strength_lte is not None:
                if int(engine.get_effective_strength(uid)) > int(target.card_filter.strength_lte):
                    continue
            if target.card_filter.drawn_this_turn_only:
                drawn = engine.state.flags.get("cards_drawn_this_turn", {})
                if uid not in set(drawn.get(str(owner_idx), [])):
                    continue
            out.append(uid)
        return out

    def _validate_manual_target_actions(
        self,
        engine: GameEngine,
        owner_idx: int,
        source_uid: str,
        actions: list[ActionSpec],
        selected_target: str | None,
        event_name: str,
        empty_pool_message: str,
        missing_selection_message: str,
    ) -> tuple[bool, str | None]:
        flags = engine.state.flags
        previous_source = flags.get("_runtime_source_card")
        previous_selected = flags.get("_runtime_selected_target")
        previous_action_idx = flags.get("_runtime_action_index")

        flags["_runtime_source_card"] = source_uid
        flags["_runtime_selected_target"] = str(selected_target or "")
        try:
            for i, action in enumerate(actions):
                if not self._target_requires_manual_selection(action.target):
                    continue
                flags["_runtime_action_index"] = str(i)
                if action.condition and not self._eval_condition_node(
                    RuleEventContext(engine=engine, event=event_name, player_idx=owner_idx, payload={"card": source_uid}),
                    owner_idx,
                    action.condition,
                ):
                    continue

                required_min = self._required_min_targets_for_manual_target(action.target)
                selectable = self._collect_selectable_targets_for_manual_target(engine, owner_idx, action.target)
                if len(selectable) < required_min:
                    return (False, empty_pool_message)

                raw_for_action = self._selected_target_raw_for_current_action(engine)
                if required_min > 0 and not raw_for_action:
                    return (False, missing_selection_message)

                resolved = self._resolve_targets(engine, owner_idx, action.target)
                if len(resolved) < required_min:
                    return (False, missing_selection_message)
            return (True, None)
        finally:
            if previous_source is None:
                flags.pop("_runtime_source_card", None)
            else:
                flags["_runtime_source_card"] = previous_source
            if previous_selected is None:
                flags.pop("_runtime_selected_target", None)
            else:
                flags["_runtime_selected_target"] = previous_selected
            if previous_action_idx is None:
                flags.pop("_runtime_action_index", None)
            else:
                flags["_runtime_action_index"] = previous_action_idx
