from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from holywar.effects.card_scripts_loader import iter_card_scripts
from holywar.effects import runtime_ported
from holywar.effects.registry import NOT_HANDLED, get_activate, get_enter, get_play

if TYPE_CHECKING:
    from holywar.core.engine import GameEngine
    from holywar.scripting_api import RuleEventContext


SUPPORTED_CONDITION_KEYS = {
    "all_of",
    "any_of",
    "not",
    "payload_from_zone_in",
    "payload_to_zone_in",
    "event_card_owner",
    "event_card_type_in",
    "turn_scope",
    "phase_is",
    "source_on_field",
    "my_saints_gte",
    "my_saints_lte",
    "opponent_saints_gte",
    "opponent_saints_lte",
    "my_inspiration_gte",
    "my_inspiration_lte",
    "opponent_inspiration_gte",
    "my_sin_gte",
    "my_sin_lte",
    "opponent_sin_gte",
    "opponent_sin_lte",
    "payload_reason_in",
}

EFFECT_ACTION_ALIASES = {
    "add_faith": "increase_faith",
    "buff_faith": "increase_faith",
    "remove_faith": "decrease_faith",
    "damage_faith": "decrease_faith",
    "buff_strength": "increase_strength",
    "add_strength": "increase_strength",
    "remove_strength": "decrease_strength",
    "draw_extra_card": "draw_cards",
    "add_draw": "draw_cards",
    "deal_sin": "inflict_sin",
    "add_sin": "inflict_sin",
    "reduce_sin": "remove_sin",
    "gain_inspiration": "add_inspiration",
    "pay_inspiration": "pay_inspiration",
}

SUPPORTED_EFFECT_ACTIONS = {
    "increase_faith",
    "decrease_faith",
    "increase_strength",
    "calice_upkeep",
    "calice_endturn",
    "campana_add_counter",
    "cataclisma_ciclico",
    "kah_ok_tick",
    "trombe_del_giudizio_tick",
    "av_drna_on_opponent_draw",
    "deriu_hebet_tick",
    "pay_sin_or_destroy_self",
    "tikal_tick",
    "mill_cards",
    "draw_cards",
    "inflict_sin",
    "remove_sin",
    "add_inspiration",
    "pay_inspiration",
}


def _norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


@dataclass(slots=True)
class TriggerSpec:
    event: str
    frequency: str = "each_turn"
    condition: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CardFilterSpec:
    name_contains: str | None = None
    card_type_in: list[str] = field(default_factory=list)
    exclude_event_card: bool = False
    crosses_gte: int | None = None
    crosses_lte: int | None = None


@dataclass(slots=True)
class TargetSpec:
    type: str
    card_filter: CardFilterSpec = field(default_factory=CardFilterSpec)
    zone: str = "field"
    owner: str = "me"


@dataclass(slots=True)
class EffectSpec:
    action: str
    amount: int = 0
    duration: str = "permanent"
    amount_multiplier_card_name: str | None = None
    once_per_turn_group: str | None = None
    target_player: str | None = None


@dataclass(slots=True)
class TriggeredEffectSpec:
    trigger: TriggerSpec
    target: TargetSpec
    effect: EffectSpec


@dataclass(slots=True)
class ActionSpec:
    target: TargetSpec
    effect: EffectSpec


@dataclass(slots=True)
class CardScript:
    name: str
    on_play_mode: str = "auto"
    on_enter_mode: str = "auto"
    on_activate_mode: str = "auto"
    triggered_effects: list[TriggeredEffectSpec] = field(default_factory=list)
    on_play_actions: list[ActionSpec] = field(default_factory=list)


class RuntimeCardManager:
    def __init__(self) -> None:
        self._scripts: dict[str, CardScript] = {}
        self._bindings: dict[int, dict[str, list[tuple[str, Callable[[RuleEventContext], None]]]]] = {}
        self._subscribed_engines: set[int] = set()
        self._temp_faith: dict[int, dict[str, list[tuple[str, int, str]]]] = {}
        self._bootstrap_from_cards_json()
        self._bootstrap_from_script_files()

    def clear_for_tests(self) -> None:
        self._scripts.clear()
        self._bindings.clear()
        self._subscribed_engines.clear()
        self._temp_faith.clear()

    def _bootstrap_from_cards_json(self) -> None:
        cards_path = Path(__file__).resolve().parents[1] / "data" / "cards.json"
        if not cards_path.exists():
            return
        try:
            rows = json.loads(cards_path.read_text(encoding="utf-8"))
        except Exception:
            return
        if not isinstance(rows, list):
            return
        for row in rows:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name", "")).strip()
            if not name:
                continue
            key = _norm(name)
            if key not in self._scripts:
                self._scripts[key] = CardScript(name=name)

    def register_script(self, script: CardScript) -> None:
        self._scripts[_norm(script.name)] = script

    def register_script_from_dict(self, card_name: str, spec: dict[str, Any]) -> None:
        def _parse_effect(raw: dict[str, Any]) -> EffectSpec:
            return EffectSpec(
                action=str(raw.get("action", "")),
                amount=int(raw.get("amount", 0)),
                duration=str(raw.get("duration", "permanent")),
                amount_multiplier_card_name=str(raw.get("amount_multiplier_card_name"))
                if raw.get("amount_multiplier_card_name") is not None
                else None,
                once_per_turn_group=str(raw.get("once_per_turn_group"))
                if raw.get("once_per_turn_group") is not None
                else None,
                target_player=str(raw.get("target_player")) if raw.get("target_player") is not None else None,
            )

        def _parse_target(raw: dict[str, Any]) -> TargetSpec:
            filt = raw.get("card_filter", {}) or {}
            return TargetSpec(
                type=str(raw.get("type", "cards_controlled_by_owner")),
                card_filter=CardFilterSpec(
                    name_contains=filt.get("name_contains"),
                    card_type_in=list(filt.get("card_type_in", []) or []),
                    exclude_event_card=bool(filt.get("exclude_event_card", False)),
                    crosses_gte=(int(filt["crosses_gte"]) if filt.get("crosses_gte") is not None else None),
                    crosses_lte=(int(filt["crosses_lte"]) if filt.get("crosses_lte") is not None else None),
                ),
                zone=str(raw.get("zone", "field")),
                owner=str(raw.get("owner", "me")),
            )

        trig_specs: list[TriggeredEffectSpec] = []
        for t in spec.get("triggered_effects", []):
            trig = TriggerSpec(
                event=str(t.get("trigger", {}).get("event", "")),
                frequency=str(t.get("trigger", {}).get("frequency", "each_turn")),
                condition=dict(t.get("trigger", {}).get("condition", {}) or {}),
            )
            target = _parse_target(t.get("target", {}) or {})
            effect = _parse_effect(t.get("effect", {}) or {})
            trig_specs.append(TriggeredEffectSpec(trigger=trig, target=target, effect=effect))
        on_play_actions: list[ActionSpec] = []
        for a in spec.get("on_play_actions", []):
            target = _parse_target(a.get("target", {}) or {})
            effect = _parse_effect(a.get("effect", {}) or {})
            on_play_actions.append(ActionSpec(target=target, effect=effect))
        self.register_script(
            CardScript(
                name=card_name,
                on_play_mode=str(spec.get("on_play_mode", "auto")),
                on_enter_mode=str(spec.get("on_enter_mode", "auto")),
                on_activate_mode=str(spec.get("on_activate_mode", "auto")),
                triggered_effects=trig_specs,
                on_play_actions=on_play_actions,
            )
        )

    def _bootstrap_from_script_files(self) -> None:
        for card_name, spec in iter_card_scripts():
            key = _norm(card_name)
            existing = self._scripts.get(key)
            if existing is not None:
                has_custom = bool(existing.triggered_effects or existing.on_play_actions)
                has_non_auto_modes = any(
                    _norm(mode) != "auto"
                    for mode in (existing.on_play_mode, existing.on_enter_mode, existing.on_activate_mode)
                )
                if has_custom or has_non_auto_modes:
                    continue
            self.register_script_from_dict(card_name, spec)

    def ensure_all_cards_migrated(self, engine: GameEngine) -> None:
        if not self._scripts:
            self._bootstrap_from_cards_json()
        self._bootstrap_from_script_files()
        for inst in engine.state.instances.values():
            key = _norm(inst.definition.name)
            if key not in self._scripts:
                self._scripts[key] = CardScript(name=inst.definition.name)
        self._ensure_leave_subscription(engine)

    def is_migrated(self, card_name: str) -> bool:
        return _norm(card_name) in self._scripts

    def migrated_count(self) -> int:
        return len(self._scripts)

    def resolve_play(self, engine: GameEngine, player_idx: int, uid: str, target: str | None) -> object:
        self.ensure_all_cards_migrated(engine)
        inst = engine.state.instances[uid]
        script = self._scripts.get(_norm(inst.definition.name), CardScript(name=inst.definition.name))
        mode = _norm(script.on_play_mode)

        if mode in {"scripted", "custom"} and script.on_play_actions:
            self._run_play_actions(engine, player_idx, uid, script.on_play_actions)
            return f"{inst.definition.name}: effetto risolto via script."
        if mode == "auto" and script.on_play_actions:
            self._run_play_actions(engine, player_idx, uid, script.on_play_actions)
            return f"{inst.definition.name}: effetto risolto via script."

        if mode in {"registry", "auto", "custom"}:
            handler = get_play(inst.definition.name)
            if handler is not None:
                out = handler(engine, player_idx, uid, target)
                if out is not NOT_HANDLED:
                    return str(out)
        if mode in {"ported", "auto", "runtime"}:
            return runtime_ported.resolve_card_effect(engine, player_idx, uid, target)
        return runtime_ported.resolve_card_effect(engine, player_idx, uid, target)

    def _run_play_actions(self, engine: GameEngine, owner_idx: int, source_uid: str, actions: list[ActionSpec]) -> None:
        for action in actions:
            targets = self._resolve_targets(engine, owner_idx, action.target)
            self._apply_effect(engine, owner_idx, source_uid, targets, action.effect)

    def resolve_enter(self, engine: GameEngine, player_idx: int, uid: str) -> object:
        self.ensure_all_cards_migrated(engine)
        self.on_enter_bind_triggers(engine, player_idx, uid)
        inst = engine.state.instances[uid]
        script = self._scripts.get(_norm(inst.definition.name), CardScript(name=inst.definition.name))
        mode = _norm(script.on_enter_mode)

        if mode in {"registry", "auto", "custom"}:
            handler = get_enter(inst.definition.name)
            if handler is not None:
                out = handler(engine, player_idx, uid)
                if out is not NOT_HANDLED:
                    return str(out)
        if mode in {"ported", "auto", "runtime"}:
            return runtime_ported.resolve_enter_effect(engine, player_idx, uid)
        return runtime_ported.resolve_enter_effect(engine, player_idx, uid)

    def resolve_activate(self, engine: GameEngine, player_idx: int, uid: str, target: str | None) -> object:
        self.ensure_all_cards_migrated(engine)
        inst = engine.state.instances[uid]
        script = self._scripts.get(_norm(inst.definition.name), CardScript(name=inst.definition.name))
        mode = _norm(script.on_activate_mode)

        if mode in {"registry", "auto", "custom"}:
            handler = get_activate(inst.definition.name)
            if handler is not None:
                out = handler(engine, player_idx, uid, target)
                if out is not NOT_HANDLED:
                    return str(out)
        if mode in {"ported", "auto", "runtime"}:
            return runtime_ported.resolve_activated_effect(engine, player_idx, uid, target)
        return runtime_ported.resolve_activated_effect(engine, player_idx, uid, target)

    def on_enter_bind_triggers(self, engine: GameEngine, owner_idx: int, source_uid: str) -> None:
        self.ensure_all_cards_migrated(engine)
        script = self._scripts.get(_norm(engine.state.instances[source_uid].definition.name))
        if not script or not script.triggered_effects:
            return
        eng_key = id(engine)
        by_source = self._bindings.setdefault(eng_key, {})
        by_source[source_uid] = []

        api = engine.rules_api(owner_idx)

        for te in script.triggered_effects:
            event_name = te.trigger.event

            def _handler(ctx: RuleEventContext, _te=te, _owner=owner_idx, _source=source_uid):
                if not self._is_uid_on_field(ctx.engine, _source):
                    return
                if _te.trigger.event == "on_my_turn_start" and ctx.player_idx != _owner:
                    return
                if _te.trigger.event == "on_opponent_turn_start" and ctx.player_idx != _owner:
                    return
                if not self._event_matches(ctx, _owner, _te.trigger.condition):
                    return
                ctx.engine.state.flags["_runtime_event_card"] = str(ctx.payload.get("card", ""))
                ctx.engine.state.flags["_runtime_event_name"] = str(ctx.event)
                try:
                    targets = self._resolve_targets(ctx.engine, _owner, _te.target)
                    self._apply_effect(ctx.engine, _owner, _source, targets, _te.effect)
                finally:
                    ctx.engine.state.flags.pop("_runtime_event_card", None)
                    ctx.engine.state.flags.pop("_runtime_event_name", None)

            api.subscribe(event_name, _handler)
            by_source[source_uid].append((event_name, _handler))

    def _ensure_leave_subscription(self, engine: GameEngine) -> None:
        key = id(engine)
        if key in self._subscribed_engines:
            return
        self._subscribed_engines.add(key)
        engine.rules_api(0).subscribe("on_this_card_leaves_field", self._on_source_leaves_field)

    def _on_source_leaves_field(self, ctx: RuleEventContext) -> None:
        source_uid = str(ctx.payload.get("card", ""))
        if not source_uid:
            return
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

    def _resolve_targets(self, engine: GameEngine, owner_idx: int, target: TargetSpec) -> list[str]:
        pool: list[str] = []
        ttype = _norm(target.type)
        if ttype == "cards_controlled_by_owner":
            real_owner = owner_idx if _norm(target.owner) in {"me", "owner", "controller"} else 1 - owner_idx
            p = engine.state.players[real_owner]
            zone = _norm(target.zone)
            if zone == "field":
                for uid in p.attack + p.defense + p.artifacts:
                    if uid:
                        pool.append(uid)
                if p.building:
                    pool.append(p.building)
            elif zone == "hand":
                pool.extend(p.hand)
            elif zone in {"deck", "relicario"}:
                pool.extend(p.deck)
            elif zone == "graveyard":
                pool.extend(p.graveyard)
        elif ttype == "all_saints_on_field":
            pool.extend(engine.all_saints_on_field(0))
            pool.extend(engine.all_saints_on_field(1))
        else:
            return []

        needle = _norm(target.card_filter.name_contains or "")
        type_filter = {_norm(v) for v in target.card_filter.card_type_in}
        event_uid = str(engine.state.flags.get("_runtime_event_card", ""))
        out: list[str] = []
        for uid in pool:
            if target.card_filter.exclude_event_card and event_uid and uid == event_uid:
                continue
            inst = engine.state.instances[uid]
            if needle and needle not in _norm(inst.definition.name):
                continue
            if type_filter and _norm(inst.definition.card_type) not in type_filter:
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
            out.append(uid)
        return out

    def _apply_effect(
        self,
        engine: GameEngine,
        owner_idx: int,
        source_uid: str,
        targets: list[str],
        effect: EffectSpec,
    ) -> None:
        action = _norm(effect.action)
        action = EFFECT_ACTION_ALIASES.get(action, action)
        if effect.once_per_turn_group:
            group_key = f"runtime_once:{_norm(effect.once_per_turn_group)}:{owner_idx}:{engine.state.turn_number}"
            done = engine.state.flags.setdefault("runtime_once", {})
            if done.get(group_key, False):
                return
            done[group_key] = True
        if action == "increase_faith":
            for t_uid in targets:
                inst = engine.state.instances[t_uid]
                inst.current_faith = (inst.current_faith or 0) + int(effect.amount)
                if _norm(effect.duration) in {"until_source_leaves", "while_source_on_field", "source_bound"}:
                    marker = f"runtime_faith:{source_uid}:{int(effect.amount)}"
                    inst.blessed.append(marker)
                    ek = id(engine)
                    by_source = self._temp_faith.setdefault(ek, {}).setdefault(source_uid, [])
                    by_source.append((t_uid, int(effect.amount), marker))
            return
        if action == "increase_strength":
            for t_uid in targets:
                engine.state.instances[t_uid].blessed.append(f"buff_str:{int(effect.amount)}")
            return
        if action == "decrease_faith":
            amount = int(effect.amount)
            if effect.amount_multiplier_card_name:
                amount *= self._count_named_cards_on_field(engine, effect.amount_multiplier_card_name)
            if amount <= 0:
                return
            for t_uid in targets:
                inst = engine.state.instances[t_uid]
                inst.current_faith = max(0, (inst.current_faith or 0) - amount)
            return
        if action == "calice_upkeep":
            player = engine.state.players[owner_idx]
            if player.sin >= 5:
                player.sin -= 5
                engine.state.log(f"{player.name} paga 5 Peccato per mantenere Calice Insanguinato.")
            else:
                engine.send_to_graveyard(owner_idx, source_uid)
                engine.state.log(f"{player.name} non puo pagare Calice Insanguinato: la carta viene distrutta.")
            return
        if action == "calice_endturn":
            destroyed = 0
            for s_uid in list(engine.all_saints_on_field(owner_idx)):
                if _norm(engine.state.instances[s_uid].definition.name) != _norm("Spirito Vacuo"):
                    continue
                engine.destroy_saint_by_uid(owner_idx, s_uid, cause="effect")
                destroyed += 1
            if destroyed > 0:
                engine.gain_sin(1 - owner_idx, destroyed * 5)
            return
        if action == "campana_add_counter":
            inst = engine.state.instances[source_uid]
            counter = 0
            for tag in list(inst.blessed):
                if tag.startswith("campana_counter:"):
                    try:
                        counter = int(tag.split(":", 1)[1])
                    except ValueError:
                        counter = 0
                    inst.blessed.remove(tag)
            counter += 1
            inst.blessed.append(f"campana_counter:{counter}")
            return
        if action == "cataclisma_ciclico":
            own_saints = engine.all_saints_on_field(owner_idx)
            opp_idx = 1 - owner_idx
            opp_saints = engine.all_saints_on_field(opp_idx)
            if not own_saints and not opp_saints:
                return
            if opp_saints:
                target_uid = opp_saints[0]
                target_owner = opp_idx
            else:
                target_uid = own_saints[0]
                target_owner = owner_idx
            target_name = engine.state.instances[target_uid].definition.name
            engine.destroy_saint_by_uid(target_owner, target_uid, cause="effect")
            if target_owner == owner_idx:
                engine.gain_sin(opp_idx, 2)
                engine.state.log(
                    f"Cataclisma Ciclico distrugge {target_name}: +2 Peccato a {engine.state.players[opp_idx].name}."
                )
            else:
                engine.reduce_sin(owner_idx, 1)
                engine.state.log(
                    f"Cataclisma Ciclico distrugge {target_name}: {engine.state.players[owner_idx].name} perde 1 Peccato."
                )
            return
        if action == "kah_ok_tick":
            inst = engine.state.instances[source_uid]
            inst.current_faith = (inst.current_faith or 0) + 2
            if (inst.current_faith or 0) >= 10:
                gained = max(0, inst.current_faith or 0)
                engine.destroy_saint_by_uid(owner_idx, source_uid, cause="effect")
                engine.gain_sin(owner_idx, gained)
                engine.state.log(
                    f"Kah-ok raggiunge 10 Fede e si distrugge: {engine.state.players[owner_idx].name} +{gained} Peccato."
                )
            return
        if action == "trombe_del_giudizio_tick":
            if not engine._has_building(owner_idx, "Altare dei Sette Sigilli"):
                return
            seals = engine._get_altare_sigilli(owner_idx)
            if seals >= 7:
                amount = 10
            elif seals >= 5:
                amount = 6
            elif seals >= 3:
                amount = 3
            else:
                amount = 0
            if amount > 0:
                engine.gain_sin(1 - owner_idx, amount)
            return
        if action == "av_drna_on_opponent_draw":
            inst = engine.state.instances[source_uid]
            inst.current_faith = max(0, (inst.current_faith or 0) - 1)
            engine.reduce_sin(owner_idx, 2)
            if (inst.current_faith or 0) <= 0:
                engine.send_to_graveyard(owner_idx, source_uid)
            return
        if action == "deriu_hebet_tick":
            player = engine.state.players[owner_idx]
            if not player.deck:
                return
            top_uid = player.deck[-1]
            ctype = _norm(engine.state.instances[top_uid].definition.card_type)
            if ctype in {"benedizione", "maledizione"}:
                engine.move_deck_card_to_hand(owner_idx, top_uid)
            else:
                engine.rng.shuffle(player.deck)
            return
        if action == "pay_sin_or_destroy_self":
            cost = max(0, int(effect.amount))
            player = engine.state.players[owner_idx]
            if player.sin >= cost:
                player.sin -= cost
            else:
                engine.send_to_graveyard(owner_idx, source_uid)
            return
        if action == "tikal_tick":
            player = engine.state.players[owner_idx]
            if not player.deck:
                return
            top_uid = player.deck[-1]
            ctype = _norm(engine.state.instances[top_uid].definition.card_type)
            if ctype == "santo":
                engine.move_deck_card_to_hand(owner_idx, top_uid)
            else:
                player.deck.pop()
                player.deck.insert(0, top_uid)
            return
        if action == "mill_cards":
            target = self._resolve_player_scope(owner_idx, effect.target_player or "opponent")
            player = engine.state.players[target]
            for _ in range(max(0, int(effect.amount))):
                if not player.deck:
                    break
                uid = player.deck.pop()
                player.graveyard.append(uid)
            return
        if action == "draw_cards":
            target = self._resolve_player_scope(owner_idx, effect.target_player)
            engine.draw_cards(target, max(0, int(effect.amount or 1)))
            return
        if action == "inflict_sin":
            target = self._resolve_player_scope(owner_idx, effect.target_player or "opponent")
            engine.gain_sin(target, max(0, int(effect.amount)))
            return
        if action == "remove_sin":
            target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            engine.reduce_sin(target, max(0, int(effect.amount)))
            return
        if action == "add_inspiration":
            target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            player = engine.state.players[target]
            player.inspiration = max(0, int(player.inspiration) + int(effect.amount))
            return
        if action == "pay_inspiration":
            target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            player = engine.state.players[target]
            player.inspiration = max(0, int(player.inspiration) - max(0, int(effect.amount)))
            return

    @staticmethod
    def _resolve_player_scope(owner_idx: int, scope: str | None) -> int:
        key = _norm(scope or "me")
        if key in {"me", "owner", "controller", "self"}:
            return owner_idx
        if key in {"opponent", "enemy", "other"}:
            return 1 - owner_idx
        if key in {"player0", "p0", "0"}:
            return 0
        if key in {"player1", "p1", "1"}:
            return 1
        return owner_idx

    def _count_named_cards_on_field(self, engine: GameEngine, card_name: str) -> int:
        key = _norm(card_name)
        total = 0
        for idx in (0, 1):
            p = engine.state.players[idx]
            for uid in p.attack + p.defense + p.artifacts:
                if uid and _norm(engine.state.instances[uid].definition.name) == key:
                    total += 1
            if p.building and _norm(engine.state.instances[p.building].definition.name) == key:
                total += 1
        return total

    def _event_matches(self, ctx: "RuleEventContext", owner_idx: int, condition: dict[str, Any]) -> bool:
        if not condition:
            return True
        return self._eval_condition_node(ctx, owner_idx, condition)

    def _eval_condition_node(self, ctx: "RuleEventContext", owner_idx: int, node: dict[str, Any]) -> bool:
        if not node:
            return True
        all_of = node.get("all_of")
        if isinstance(all_of, list):
            for sub in all_of:
                if isinstance(sub, dict) and not self._eval_condition_node(ctx, owner_idx, sub):
                    return False
        any_of = node.get("any_of")
        if isinstance(any_of, list) and any_of:
            ok = False
            for sub in any_of:
                if isinstance(sub, dict) and self._eval_condition_node(ctx, owner_idx, sub):
                    ok = True
                    break
            if not ok:
                return False
        not_of = node.get("not")
        if isinstance(not_of, dict) and self._eval_condition_node(ctx, owner_idx, not_of):
            return False
        return self._eval_condition_leaf(ctx, owner_idx, node)

    def _eval_condition_leaf(self, ctx: "RuleEventContext", owner_idx: int, condition: dict[str, Any]) -> bool:
        payload = ctx.payload
        event_card_uid = str(payload.get("card", ""))

        from_zone_in = condition.get("payload_from_zone_in")
        if from_zone_in:
            from_zone = _norm(str(payload.get("from_zone", "")))
            allowed = {_norm(z) for z in from_zone_in}
            if from_zone not in allowed:
                return False

        to_zone_in = condition.get("payload_to_zone_in")
        if to_zone_in:
            to_zone = _norm(str(payload.get("to_zone", payload.get("destination", ""))))
            allowed_to = {_norm(z) for z in to_zone_in}
            if to_zone not in allowed_to:
                return False

        owner_rule = _norm(str(condition.get("event_card_owner", "")))
        if owner_rule and event_card_uid:
            inst = ctx.engine.state.instances.get(event_card_uid)
            if inst is None:
                return False
            expected_owner = owner_idx if owner_rule in {"me", "owner", "controller"} else (1 - owner_idx)
            if int(inst.owner) != int(expected_owner):
                return False

        ctype_in = condition.get("event_card_type_in")
        if ctype_in and event_card_uid:
            inst = ctx.engine.state.instances.get(event_card_uid)
            if inst is None:
                return False
            allowed_types = {_norm(v) for v in ctype_in}
            if _norm(inst.definition.card_type) not in allowed_types:
                return False

        turn_scope = _norm(str(condition.get("turn_scope", "")))
        if turn_scope:
            if turn_scope in {"my", "owner", "controller"} and int(ctx.engine.state.active_player) != int(owner_idx):
                return False
            if turn_scope in {"opponent", "enemy"} and int(ctx.engine.state.active_player) == int(owner_idx):
                return False

        phase_is = _norm(str(condition.get("phase_is", "")))
        if phase_is:
            runtime_state = ctx.engine.state.flags.setdefault("runtime_state", {})
            current_phase = _norm(str(runtime_state.get("phase", "")))
            if phase_is != current_phase:
                return False

        if condition.get("source_on_field") is True and not self._is_uid_on_field(ctx.engine, str(payload.get("source", ""))):
            return False

        my_saints_gte = condition.get("my_saints_gte")
        if my_saints_gte is not None and len(ctx.engine.all_saints_on_field(owner_idx)) < int(my_saints_gte):
            return False
        my_saints_lte = condition.get("my_saints_lte")
        if my_saints_lte is not None and len(ctx.engine.all_saints_on_field(owner_idx)) > int(my_saints_lte):
            return False
        opp = 1 - owner_idx
        opp_saints_gte = condition.get("opponent_saints_gte")
        if opp_saints_gte is not None and len(ctx.engine.all_saints_on_field(opp)) < int(opp_saints_gte):
            return False
        opp_saints_lte = condition.get("opponent_saints_lte")
        if opp_saints_lte is not None and len(ctx.engine.all_saints_on_field(opp)) > int(opp_saints_lte):
            return False

        my_insp_gte = condition.get("my_inspiration_gte")
        if my_insp_gte is not None and int(ctx.engine.state.players[owner_idx].inspiration) < int(my_insp_gte):
            return False
        my_insp_lte = condition.get("my_inspiration_lte")
        if my_insp_lte is not None and int(ctx.engine.state.players[owner_idx].inspiration) > int(my_insp_lte):
            return False
        opp_insp_gte = condition.get("opponent_inspiration_gte")
        if opp_insp_gte is not None and int(ctx.engine.state.players[opp].inspiration) < int(opp_insp_gte):
            return False
        my_sin_gte = condition.get("my_sin_gte")
        if my_sin_gte is not None and int(ctx.engine.state.players[owner_idx].sin) < int(my_sin_gte):
            return False
        my_sin_lte = condition.get("my_sin_lte")
        if my_sin_lte is not None and int(ctx.engine.state.players[owner_idx].sin) > int(my_sin_lte):
            return False
        opp_sin_gte = condition.get("opponent_sin_gte")
        if opp_sin_gte is not None and int(ctx.engine.state.players[opp].sin) < int(opp_sin_gte):
            return False
        opp_sin_lte = condition.get("opponent_sin_lte")
        if opp_sin_lte is not None and int(ctx.engine.state.players[opp].sin) > int(opp_sin_lte):
            return False

        reason_in = condition.get("payload_reason_in")
        if reason_in:
            reason = _norm(str(payload.get("reason", "")))
            allowed_reason = {_norm(v) for v in reason_in}
            if reason not in allowed_reason:
                return False
        return True


runtime_cards = RuntimeCardManager()


__all__ = [
    "TriggerSpec",
    "CardFilterSpec",
    "TargetSpec",
    "EffectSpec",
    "TriggeredEffectSpec",
    "ActionSpec",
    "CardScript",
    "RuntimeCardManager",
    "runtime_cards",
]
