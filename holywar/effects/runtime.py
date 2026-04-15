from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from holywar.effects import runtime_ported
from holywar.effects.registry import NOT_HANDLED, get_activate, get_enter, get_play

if TYPE_CHECKING:
    from holywar.core.engine import GameEngine
    from holywar.scripting_api import RuleEventContext


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


@dataclass(slots=True)
class TriggeredEffectSpec:
    trigger: TriggerSpec
    target: TargetSpec
    effect: EffectSpec


@dataclass(slots=True)
class CardScript:
    name: str
    on_play_mode: str = "auto"
    on_enter_mode: str = "auto"
    on_activate_mode: str = "auto"
    triggered_effects: list[TriggeredEffectSpec] = field(default_factory=list)


class RuntimeCardManager:
    def __init__(self) -> None:
        self._scripts: dict[str, CardScript] = {}
        self._bindings: dict[int, dict[str, list[tuple[str, Callable[[RuleEventContext], None]]]]] = {}
        self._subscribed_engines: set[int] = set()
        self._temp_faith: dict[int, dict[str, list[tuple[str, int, str]]]] = {}
        self._bootstrap_from_cards_json()

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
        trig_specs: list[TriggeredEffectSpec] = []
        for t in spec.get("triggered_effects", []):
            trig = TriggerSpec(
                event=str(t.get("trigger", {}).get("event", "")),
                frequency=str(t.get("trigger", {}).get("frequency", "each_turn")),
                condition=dict(t.get("trigger", {}).get("condition", {}) or {}),
            )
            filt = t.get("target", {}).get("card_filter", {}) or {}
            target = TargetSpec(
                type=str(t.get("target", {}).get("type", "cards_controlled_by_owner")),
                card_filter=CardFilterSpec(
                    name_contains=filt.get("name_contains"),
                    card_type_in=list(filt.get("card_type_in", []) or []),
                    exclude_event_card=bool(filt.get("exclude_event_card", False)),
                    crosses_gte=(
                        int(filt["crosses_gte"]) if filt.get("crosses_gte") is not None else None
                    ),
                    crosses_lte=(
                        int(filt["crosses_lte"]) if filt.get("crosses_lte") is not None else None
                    ),
                ),
                zone=str(t.get("target", {}).get("zone", "field")),
                owner=str(t.get("target", {}).get("owner", "me")),
            )
            eff = t.get("effect", {}) or {}
            effect = EffectSpec(
                action=str(eff.get("action", "")),
                amount=int(eff.get("amount", 0)),
                duration=str(eff.get("duration", "permanent")),
                amount_multiplier_card_name=str(eff.get("amount_multiplier_card_name"))
                if eff.get("amount_multiplier_card_name") is not None
                else None,
                once_per_turn_group=str(eff.get("once_per_turn_group"))
                if eff.get("once_per_turn_group") is not None
                else None,
            )
            trig_specs.append(TriggeredEffectSpec(trigger=trig, target=target, effect=effect))
        self.register_script(
            CardScript(
                name=card_name,
                on_play_mode=str(spec.get("on_play_mode", "auto")),
                on_enter_mode=str(spec.get("on_enter_mode", "auto")),
                on_activate_mode=str(spec.get("on_activate_mode", "auto")),
                triggered_effects=trig_specs,
            )
        )

    def ensure_all_cards_migrated(self, engine: GameEngine) -> None:
        if not self._scripts:
            self._bootstrap_from_cards_json()
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

        if mode in {"registry", "auto", "custom"}:
            handler = get_play(inst.definition.name)
            if handler is not None:
                out = handler(engine, player_idx, uid, target)
                if out is not NOT_HANDLED:
                    return str(out)
        if mode in {"ported", "auto", "runtime"}:
            return runtime_ported.resolve_card_effect(engine, player_idx, uid, target)
        return runtime_ported.resolve_card_effect(engine, player_idx, uid, target)

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
        payload = ctx.payload
        event_card_uid = str(payload.get("card", ""))

        from_zone_in = condition.get("payload_from_zone_in")
        if from_zone_in:
            from_zone = _norm(str(payload.get("from_zone", "")))
            allowed = {_norm(z) for z in from_zone_in}
            if from_zone not in allowed:
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
        return True


runtime_cards = RuntimeCardManager()

# Example declarative trigger structure (requested by user).
runtime_cards.register_script_from_dict(
    "Foresta Sacra",
    {
        "on_play_mode": "auto",
        "on_enter_mode": "auto",
        "on_activate_mode": "auto",
        "triggered_effects": [
            {
                "trigger": {"event": "on_my_turn_start", "frequency": "each_turn"},
                "target": {
                    "type": "cards_controlled_by_owner",
                    "card_filter": {"name_contains": "Albero"},
                    "zone": "field",
                    "owner": "me",
                },
                "effect": {"action": "increase_faith", "amount": 2, "duration": "until_source_leaves"},
            }
        ],
    },
)

runtime_cards.register_script_from_dict(
    "Saga degli Eroi Caduti",
    {
        "on_play_mode": "auto",
        "on_enter_mode": "auto",
        "on_activate_mode": "auto",
        "triggered_effects": [
            {
                "trigger": {
                    "event": "on_card_sent_to_graveyard",
                    "frequency": "each_turn",
                    "condition": {
                        "payload_from_zone_in": ["attack", "defense"],
                        "event_card_owner": "me",
                        "event_card_type_in": ["santo", "token"],
                    },
                },
                "target": {
                    "type": "cards_controlled_by_owner",
                    "card_filter": {
                        "card_type_in": ["santo", "token"],
                        "exclude_event_card": True,
                    },
                    "zone": "field",
                    "owner": "me",
                },
                "effect": {"action": "increase_strength", "amount": 1, "duration": "permanent"},
            }
        ],
    },
)

runtime_cards.register_script_from_dict(
    "Fuoco",
    {
        "on_play_mode": "auto",
        "on_enter_mode": "auto",
        "on_activate_mode": "auto",
        "triggered_effects": [
            {
                "trigger": {"event": "on_turn_end", "frequency": "each_turn"},
                "target": {
                    "type": "all_saints_on_field",
                    "card_filter": {"card_type_in": ["santo", "token"], "crosses_gte": 4},
                },
                "effect": {
                    "action": "decrease_faith",
                    "amount": 2,
                    "amount_multiplier_card_name": "Fuoco",
                    "once_per_turn_group": "fuoco_tick",
                    "duration": "permanent",
                },
            }
        ],
    },
)

runtime_cards.register_script_from_dict(
    "Calice Insanguinato",
    {
        "on_play_mode": "auto",
        "on_enter_mode": "auto",
        "on_activate_mode": "auto",
        "triggered_effects": [
            {
                "trigger": {"event": "on_my_turn_start", "frequency": "each_turn"},
                "target": {"type": "cards_controlled_by_owner", "zone": "field", "owner": "me"},
                "effect": {"action": "calice_upkeep"},
            },
            {
                "trigger": {"event": "on_turn_end", "frequency": "each_turn"},
                "target": {"type": "cards_controlled_by_owner", "zone": "field", "owner": "me"},
                "effect": {"action": "calice_endturn", "once_per_turn_group": "calice_endturn"},
            },
        ],
    },
)

runtime_cards.register_script_from_dict(
    "Campana",
    {
        "on_play_mode": "auto",
        "on_enter_mode": "auto",
        "on_activate_mode": "auto",
        "triggered_effects": [
            {
                "trigger": {"event": "on_my_turn_start", "frequency": "each_turn"},
                "target": {"type": "cards_controlled_by_owner", "zone": "field", "owner": "me"},
                "effect": {"action": "campana_add_counter"},
            }
        ],
    },
)

runtime_cards.register_script_from_dict(
    "Cataclisma Ciclico",
    {
        "on_play_mode": "auto",
        "on_enter_mode": "auto",
        "on_activate_mode": "auto",
        "triggered_effects": [
            {
                "trigger": {"event": "on_my_turn_start", "frequency": "each_turn"},
                "target": {"type": "cards_controlled_by_owner", "zone": "field", "owner": "me"},
                "effect": {"action": "cataclisma_ciclico", "once_per_turn_group": "cataclisma_tick"},
            }
        ],
    },
)


__all__ = [
    "TriggerSpec",
    "CardFilterSpec",
    "TargetSpec",
    "EffectSpec",
    "TriggeredEffectSpec",
    "CardScript",
    "RuntimeCardManager",
    "runtime_cards",
]
