from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from holywar.effects.card_scripts_loader import iter_card_scripts
from holywar.effects import runtime_ported
from holywar.effects.registry import NOT_HANDLED, get_activate, get_enter, get_play
from holywar.scripting_api import RuleEventContext

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
    "target_current_faith_gte",
    "controller_has_saint_with_name",
    "controller_has_card_in_hand_with_name",
    "controller_has_card_in_deck_with_name",
    "controller_has_distinct_saints_gte",
    "selected_target_in",
    "selected_target_startswith",
    "event_card_name_is",
    "target_is_damaged",
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
    "add_seal_counter",
    "remove_seal_counter",
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
    "remove_from_board_no_sin",
    "summon_card_from_hand",
    "summon_named_card",
    "move_source_to_board",
    "move_to_deck_bottom",
    "request_end_turn",
    "shuffle_deck",
    "swap_attack_defense",
    "increase_faith_per_opponent_saints",
    "increase_faith_if_damaged",
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
    name_not_contains: str | None = None
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
    max_targets: int | None = None


@dataclass(slots=True)
class EffectSpec:
    action: str
    amount: int = 0
    duration: str = "permanent"
    amount_multiplier_card_name: str | None = None
    once_per_turn_group: str | None = None
    target_player: str | None = None
    card_name: str | None = None


@dataclass(slots=True)
class TriggeredEffectSpec:
    trigger: TriggerSpec
    target: TargetSpec
    effect: EffectSpec


@dataclass(slots=True)
class ActionSpec:
    target: TargetSpec
    effect: EffectSpec
    condition: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CardScript:
    name: str
    on_play_mode: str = "auto"
    on_enter_mode: str = "auto"
    on_activate_mode: str = "auto"
    play_owner: str = "me"
    play_targeting: str = "auto"
    activate_targeting: str = "auto"
    attack_targeting: str = "auto"
    battle_survival_mode: str = "none"
    battle_survival_names: list[str] = field(default_factory=list)
    battle_survival_token_name: str | None = None
    battle_survival_restore_faith: int | None = None
    battle_excommunicate_on_lethal: bool = False
    post_battle_forced_destroy: bool = False
    turn_start_summon_token_name: str | None = None
    auto_play_on_draw: bool = False
    end_turn_on_draw: bool = False
    strength_bonus_rules: list[dict[str, Any]] = field(default_factory=list)
    sigilli_strength_bonus_threshold: int | None = None
    sigilli_strength_bonus_amount: int | None = None
    triggered_effects: list[TriggeredEffectSpec] = field(default_factory=list)
    on_play_actions: list[ActionSpec] = field(default_factory=list)
    on_enter_actions: list[ActionSpec] = field(default_factory=list)
    on_activate_actions: list[ActionSpec] = field(default_factory=list)


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
                card_name=str(raw.get("card_name")) if raw.get("card_name") is not None else None,
            )

        def _parse_target(raw: dict[str, Any]) -> TargetSpec:
            filt = raw.get("card_filter", {}) or {}
            return TargetSpec(
                type=str(raw.get("type", "cards_controlled_by_owner")),
                card_filter=CardFilterSpec(
                    name_contains=filt.get("name_contains"),
                    name_not_contains=filt.get("name_not_contains"),
                    card_type_in=list(filt.get("card_type_in", []) or []),
                    exclude_event_card=bool(filt.get("exclude_event_card", False)),
                    crosses_gte=(int(filt["crosses_gte"]) if filt.get("crosses_gte") is not None else None),
                    crosses_lte=(int(filt["crosses_lte"]) if filt.get("crosses_lte") is not None else None),
                ),
                zone=str(raw.get("zone", "field")),
                owner=str(raw.get("owner", "me")),
                max_targets=(int(raw["max_targets"]) if raw.get("max_targets") is not None else None),
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
            on_play_actions.append(ActionSpec(target=target, effect=effect, condition=dict(a.get("condition", {}) or {})))
        on_enter_actions: list[ActionSpec] = []
        for a in spec.get("on_enter_actions", []):
            target = _parse_target(a.get("target", {}) or {})
            effect = _parse_effect(a.get("effect", {}) or {})
            on_enter_actions.append(ActionSpec(target=target, effect=effect, condition=dict(a.get("condition", {}) or {})))
        on_activate_actions: list[ActionSpec] = []
        for a in spec.get("on_activate_actions", []):
            target = _parse_target(a.get("target", {}) or {})
            effect = _parse_effect(a.get("effect", {}) or {})
            on_activate_actions.append(
                ActionSpec(target=target, effect=effect, condition=dict(a.get("condition", {}) or {}))
            )
        self.register_script(
            CardScript(
                name=card_name,
                on_play_mode=str(spec.get("on_play_mode", "auto")),
                on_enter_mode=str(spec.get("on_enter_mode", "auto")),
                on_activate_mode=str(spec.get("on_activate_mode", "auto")),
                play_owner=str(spec.get("play_owner", "me")),
                play_targeting=str(spec.get("play_targeting", "auto")),
                activate_targeting=str(spec.get("activate_targeting", "auto")),
                attack_targeting=str(spec.get("attack_targeting", "auto")),
                battle_survival_mode=str(spec.get("battle_survival_mode", "none")),
                battle_survival_names=list(spec.get("battle_survival_names", []) or []),
                battle_survival_token_name=(
                    str(spec.get("battle_survival_token_name")) if spec.get("battle_survival_token_name") is not None else None
                ),
                battle_survival_restore_faith=(
                    int(spec.get("battle_survival_restore_faith", 0))
                    if spec.get("battle_survival_restore_faith") is not None
                    else None
                ),
                battle_excommunicate_on_lethal=bool(spec.get("battle_excommunicate_on_lethal", False)),
                post_battle_forced_destroy=bool(spec.get("post_battle_forced_destroy", False)),
                turn_start_summon_token_name=(
                    str(spec.get("turn_start_summon_token_name")) if spec.get("turn_start_summon_token_name") is not None else None
                ),
                auto_play_on_draw=bool(spec.get("auto_play_on_draw", False)),
                end_turn_on_draw=bool(spec.get("end_turn_on_draw", False)),
                strength_bonus_rules=[dict(rule) for rule in spec.get("strength_bonus_rules", []) if isinstance(rule, dict)],
                sigilli_strength_bonus_threshold=(
                    int(spec["sigilli_strength_bonus_threshold"])
                    if spec.get("sigilli_strength_bonus_threshold") is not None
                    else None
                ),
                sigilli_strength_bonus_amount=(
                    int(spec["sigilli_strength_bonus_amount"])
                    if spec.get("sigilli_strength_bonus_amount") is not None
                    else None
                ),
                triggered_effects=trig_specs,
                on_play_actions=on_play_actions,
                on_enter_actions=on_enter_actions,
                on_activate_actions=on_activate_actions,
            )
        )

    def _bootstrap_from_script_files(self) -> None:
        for card_name, spec in iter_card_scripts():
            key = _norm(card_name)
            existing = self._scripts.get(key)
            if existing is not None:
                has_custom = bool(existing.triggered_effects or existing.on_play_actions or existing.on_activate_actions)
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

    def get_script(self, card_name: str) -> CardScript | None:
        return self._scripts.get(_norm(card_name))

    def get_play_targeting_mode(self, card_name: str) -> str:
        script = self.get_script(card_name)
        if script is None:
            return "auto"
        return str(script.play_targeting or "auto").strip().lower() or "auto"

    def get_play_owner(self, card_name: str) -> str:
        script = self.get_script(card_name)
        if script is None:
            return "me"
        return str(script.play_owner or "me").strip().lower() or "me"

    def get_activate_targeting_mode(self, card_name: str) -> str:
        script = self.get_script(card_name)
        if script is None:
            return "auto"
        return str(script.activate_targeting or "auto").strip().lower() or "auto"

    def get_attack_targeting_mode(self, card_name: str) -> str:
        script = self.get_script(card_name)
        if script is None:
            return "auto"
        return str(script.attack_targeting or "auto").strip().lower() or "auto"

    def get_battle_survival_mode(self, card_name: str) -> str:
        script = self.get_script(card_name)
        if script is None:
            return "none"
        return str(script.battle_survival_mode or "none").strip().lower() or "none"

    def get_battle_survival_names(self, card_name: str) -> list[str]:
        script = self.get_script(card_name)
        if script is None:
            return []
        return [str(name) for name in script.battle_survival_names if str(name).strip()]

    def get_battle_survival_token_name(self, card_name: str) -> str | None:
        script = self.get_script(card_name)
        if script is None:
            return None
        value = str(script.battle_survival_token_name or "").strip()
        return value or None

    def get_battle_survival_restore_faith(self, card_name: str) -> int | None:
        script = self.get_script(card_name)
        if script is None:
            return None
        return script.battle_survival_restore_faith

    def get_battle_excommunicate_on_lethal(self, card_name: str) -> bool:
        script = self.get_script(card_name)
        if script is None:
            return False
        return bool(script.battle_excommunicate_on_lethal)

    def get_post_battle_forced_destroy(self, card_name: str) -> bool:
        script = self.get_script(card_name)
        if script is None:
            return False
        return bool(script.post_battle_forced_destroy)

    def get_turn_start_summon_token_name(self, card_name: str) -> str | None:
        script = self.get_script(card_name)
        if script is None:
            return None
        value = str(script.turn_start_summon_token_name or "").strip()
        return value or None

    def get_auto_play_on_draw(self, card_name: str) -> bool:
        script = self.get_script(card_name)
        if script is None:
            return False
        return bool(script.auto_play_on_draw)

    def get_end_turn_on_draw(self, card_name: str) -> bool:
        script = self.get_script(card_name)
        if script is None:
            return False
        return bool(script.end_turn_on_draw)

    def get_strength_bonus_rules(self, card_name: str) -> list[dict[str, Any]]:
        script = self.get_script(card_name)
        if script is None:
            return []
        return [dict(rule) for rule in script.strength_bonus_rules]

    def get_sigilli_strength_bonus_threshold(self, card_name: str) -> int | None:
        script = self.get_script(card_name)
        if script is None:
            return None
        return script.sigilli_strength_bonus_threshold

    def get_sigilli_strength_bonus_amount(self, card_name: str) -> int | None:
        script = self.get_script(card_name)
        if script is None:
            return None
        return script.sigilli_strength_bonus_amount

    def migrated_count(self) -> int:
        return len(self._scripts)

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
            if mode in {"noop", "none"}:
                return f"{inst.definition.name}: nessun effetto all'ingresso."
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
        finally:
            if previous_source is None:
                flags.pop("_runtime_effect_source", None)
            else:
                flags["_runtime_effect_source"] = previous_source
            flags.pop("_runtime_source_card", None)
            flags.pop("_runtime_selected_target", None)

    def _run_play_actions(self, engine: GameEngine, owner_idx: int, source_uid: str, actions: list[ActionSpec]) -> None:
        for action in actions:
            if action.condition and not self._eval_condition_node(
                RuleEventContext(engine=engine, event="on_play", player_idx=owner_idx, payload={"card": source_uid}),
                owner_idx,
                action.condition,
            ):
                continue
            targets = self._resolve_targets(engine, owner_idx, action.target)
            self._apply_effect(engine, owner_idx, source_uid, targets, action.effect)

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
            if mode in {"scripted", "custom"} and script.on_enter_actions:
                self._run_enter_actions(engine, player_idx, uid, script.on_enter_actions)
                return f"{inst.definition.name}: effetto di ingresso risolto via script."
            if mode == "auto" and script.on_enter_actions:
                self._run_enter_actions(engine, player_idx, uid, script.on_enter_actions)
                return f"{inst.definition.name}: effetto di ingresso risolto via script."

            if mode in {"registry", "auto", "custom"}:
                handler = get_enter(inst.definition.name)
                if handler is not None:
                    out = handler(engine, player_idx, uid)
                    if out is not NOT_HANDLED:
                        return str(out)
            if mode in {"ported", "auto", "runtime"}:
                return runtime_ported.resolve_enter_effect(engine, player_idx, uid)
            return runtime_ported.resolve_enter_effect(engine, player_idx, uid)
        finally:
            if previous_source is None:
                flags.pop("_runtime_effect_source", None)
            else:
                flags["_runtime_effect_source"] = previous_source
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
            if mode in {"registry", "auto", "custom"}:
                handler = get_activate(inst.definition.name)
                if handler is not None:
                    out = handler(engine, player_idx, uid, target)
                    if out is not NOT_HANDLED:
                        return str(out)
            if mode in {"scripted", "custom"} and script.on_activate_actions:
                self._run_activate_actions(engine, player_idx, uid, script.on_activate_actions)
                return f"{inst.definition.name}: effetto attivato via script."
            if mode in {"ported", "auto", "runtime"}:
                return runtime_ported.resolve_activated_effect(engine, player_idx, uid, target)
            return runtime_ported.resolve_activated_effect(engine, player_idx, uid, target)
        finally:
            if previous_source is None:
                flags.pop("_runtime_effect_source", None)
            else:
                flags["_runtime_effect_source"] = previous_source
            flags.pop("_runtime_source_card", None)
            flags.pop("_runtime_selected_target", None)

    def _run_activate_actions(self, engine: GameEngine, owner_idx: int, source_uid: str, actions: list[ActionSpec]) -> None:
        for action in actions:
            if action.condition and not self._eval_condition_node(
                RuleEventContext(engine=engine, event="on_activate", player_idx=owner_idx, payload={"card": source_uid}),
                owner_idx,
                action.condition,
            ):
                continue
            targets = self._resolve_targets(engine, owner_idx, action.target)
            self._apply_effect(engine, owner_idx, source_uid, targets, action.effect)

    def _run_enter_actions(self, engine: GameEngine, owner_idx: int, source_uid: str, actions: list[ActionSpec]) -> None:
        for action in actions:
            if action.condition and not self._eval_condition_node(
                RuleEventContext(engine=engine, event="on_enter", player_idx=owner_idx, payload={"card": source_uid}),
                owner_idx,
                action.condition,
            ):
                continue
            targets = self._resolve_targets(engine, owner_idx, action.target)
            self._apply_effect(engine, owner_idx, source_uid, targets, action.effect)

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
                if _te.trigger.event == "on_my_turn_start" and ctx.player_idx != _owner:
                    return
                if _te.trigger.event == "on_opponent_turn_start" and ctx.player_idx != _owner:
                    return
                if not self._event_matches(ctx, _owner, _te.trigger.condition):
                    return
                ctx.engine.state.flags["_runtime_event_card"] = str(
                    ctx.payload.get("card", ctx.payload.get("saint", ctx.payload.get("token", "")))
                )
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
                    ctx.engine.state.flags.pop("_runtime_event_name", None)
                    ctx.engine.state.flags.pop("_runtime_source_card", None)

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
        elif ttype == "event_card":
            event_uid = str(engine.state.flags.get("_runtime_event_card", ""))
            if event_uid:
                pool.append(event_uid)
        elif ttype == "source_card":
            source_uid = str(engine.state.flags.get("_runtime_source_card", ""))
            if source_uid:
                pool.append(source_uid)
        elif ttype == "selected_target":
            selected = str(engine.state.flags.get("_runtime_selected_target", ""))
            if selected:
                if selected.startswith("buff:"):
                    selected = selected.split(":", 1)[1]
                if selected in engine.state.instances:
                    pool.append(selected)
                else:
                    zone, slot = engine._parse_zone_target(selected)
                    if zone is not None:
                        p = engine.state.players[owner_idx]
                        if zone == "attack" and 0 <= slot < len(p.attack):
                            uid = p.attack[slot]
                            if uid:
                                pool.append(uid)
                        elif zone == "defense" and 0 <= slot < len(p.defense):
                            uid = p.defense[slot]
                            if uid:
                                pool.append(uid)
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
            needle_not = _norm(target.card_filter.name_not_contains or "")
            if needle_not and needle_not in _norm(inst.definition.name):
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
        if target.max_targets is not None and target.max_targets >= 0:
            return out[: int(target.max_targets)]
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
        if action == "double_strength":
            for t_uid in targets:
                inst = engine.state.instances[t_uid]
                current = engine.get_effective_strength(t_uid)
                base = max(0, inst.definition.strength or 0)
                bonus = current - base
                inst.definition.strength = max(0, base + bonus)
                inst.blessed.append(f"buff_str:{current}")
            return
        if action == "add_seal_counter":
            amount = max(0, int(effect.amount))
            if amount <= 0:
                return
            engine._set_altare_sigilli(owner_idx, engine._get_altare_sigilli(owner_idx) + amount)
            return
        if action == "remove_seal_counter":
            amount = max(0, int(effect.amount))
            if amount <= 0:
                return
            engine._set_altare_sigilli(owner_idx, max(0, engine._get_altare_sigilli(owner_idx) - amount))
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
                if (inst.current_faith or 0) <= 0 and _norm(inst.definition.card_type) in {"santo", "token"}:
                    engine.destroy_saint_by_uid(inst.owner, t_uid, cause="effect")
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
        if action == "destroy_card":
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                engine.destroy_saint_by_uid(inst.owner, t_uid, cause="effect")
            return
        if action == "excommunicate_card":
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                engine.destroy_saint_by_uid(inst.owner, t_uid, excommunicate=True, cause="effect")
            return
        if action == "remove_from_board_no_sin":
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                engine.remove_from_board_no_sin(inst.owner, t_uid)
            return
        if action == "move_to_hand":
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                owner = inst.owner
                player = engine.state.players[owner]
                moved = False
                if t_uid in player.deck:
                    moved = engine.move_deck_card_to_hand(owner, t_uid)
                elif t_uid in player.graveyard:
                    moved = engine.move_graveyard_card_to_hand(owner, t_uid)
                if moved:
                    engine.state.log(f"{inst.definition.name} viene aggiunta alla mano.")
            return
        if action == "summon_card_from_hand":
            selected = str(engine.state.flags.get("_runtime_selected_target", "")).strip()
            card_name = _norm(effect.card_name or selected)
            if not card_name:
                return
            player = engine.state.players[owner_idx]
            chosen_uid = None
            for h_uid in list(player.hand):
                if _norm(engine.state.instances[h_uid].definition.name) == card_name:
                    chosen_uid = h_uid
                    break
            if chosen_uid is None:
                return
            slot = engine._first_open(player.attack)
            zone = "attack"
            if slot is None:
                slot = engine._first_open(player.defense)
                zone = "defense"
            if slot is None:
                return
            player.hand.remove(chosen_uid)
            if not engine.place_card_from_uid(owner_idx, chosen_uid, zone, slot):
                player.hand.append(chosen_uid)
                return
            inst = engine.state.instances[chosen_uid]
            inst.exhausted = False
            engine.state.log(f"{player.name} evoca {inst.definition.name} dalla mano.")
            engine._emit_event("on_enter_field", owner_idx, card=chosen_uid, from_zone="hand")
            engine._emit_event("on_summoned_from_hand", owner_idx, card=chosen_uid)
            if _norm(inst.definition.card_type) == _norm("token"):
                engine._emit_event("on_token_summoned", owner_idx, token=chosen_uid, summoner=owner_idx)
            else:
                engine._emit_event("on_opponent_saint_enters_field", 1 - owner_idx, saint=chosen_uid)
            enter_msg = self.resolve_enter(engine, owner_idx, chosen_uid)
            if enter_msg:
                engine.state.log(str(enter_msg))
            return
        if action == "summon_named_card":
            card_name = _norm(effect.card_name or "")
            if not card_name:
                return
            player = engine.state.players[owner_idx]
            chosen_uid = None
            for pool_name in ("hand", "deck", "graveyard", "white_deck", "excommunicated"):
                pool = getattr(player, pool_name, None)
                if pool is None:
                    continue
                for c_uid in list(pool):
                    if _norm(engine.state.instances[c_uid].definition.name) == card_name:
                        chosen_uid = c_uid
                        pool.remove(c_uid)
                        break
                if chosen_uid is not None:
                    break
            if chosen_uid is None:
                return
            slot = engine._first_open(player.attack)
            zone = "attack"
            if slot is None:
                slot = engine._first_open(player.defense)
                zone = "defense"
            if slot is None:
                return
            if not engine.place_card_from_uid(owner_idx, chosen_uid, zone, slot):
                return
            inst = engine.state.instances[chosen_uid]
            inst.exhausted = False
            engine.state.log(f"{player.name} evoca {inst.definition.name}.")
            engine._emit_event("on_enter_field", owner_idx, card=chosen_uid, from_zone="summon")
            engine._emit_event("on_summoned_from_hand", owner_idx, card=chosen_uid)
            if _norm(inst.definition.card_type) == _norm("token"):
                engine._emit_event("on_token_summoned", owner_idx, token=chosen_uid, summoner=owner_idx)
            else:
                engine._emit_event("on_opponent_saint_enters_field", 1 - owner_idx, saint=chosen_uid)
            enter_msg = self.resolve_enter(engine, owner_idx, chosen_uid)
            if enter_msg:
                engine.state.log(str(enter_msg))
            return
        if action == "move_to_deck_bottom":
            for t_uid in targets:
                inst = engine.state.instances.get(t_uid)
                if inst is None:
                    continue
                owner = inst.owner
                if engine.move_graveyard_card_to_deck_bottom(owner, t_uid):
                    engine.state.log(f"{inst.definition.name} torna nel reliquiario.")
            return
        if action == "shuffle_deck":
            target = self._resolve_player_scope(owner_idx, effect.target_player or "me")
            engine.rng.shuffle(engine.state.players[target].deck)
            return
        if action == "move_source_to_board":
            source = str(engine.state.flags.get("_runtime_source_card", ""))
            if not source or source not in engine.state.instances:
                return
            player = engine.state.players[owner_idx]
            if source not in player.hand:
                return
            slot = engine._first_open(player.attack)
            zone = "attack"
            if slot is None:
                slot = engine._first_open(player.defense)
                zone = "defense"
            if slot is None:
                return
            player.hand.remove(source)
            if not engine.place_card_from_uid(owner_idx, source, zone, slot):
                player.hand.append(source)
                return
            inst = engine.state.instances[source]
            inst.exhausted = False
            engine.state.log(f"{player.name} posiziona {inst.definition.name}.")
            engine._emit_event("on_enter_field", owner_idx, card=source, from_zone="hand")
            engine._emit_event("on_summoned_from_hand", owner_idx, card=source)
            if _norm(inst.definition.card_type) == _norm("token"):
                engine._emit_event("on_token_summoned", owner_idx, token=source, summoner=owner_idx)
            else:
                engine._emit_event("on_opponent_saint_enters_field", 1 - owner_idx, saint=source)
            enter_msg = self.resolve_enter(engine, owner_idx, source)
            if enter_msg:
                engine.state.log(str(enter_msg))
            return
        if action == "request_end_turn":
            runtime_state = engine.state.flags.setdefault("runtime_state", {})
            runtime_state["request_end_turn"] = True
            return
        if action == "swap_attack_defense":
            player = engine.state.players[owner_idx]
            attack_slot = next((i for i, uid in enumerate(player.attack) if uid is not None), None)
            defense_slot = next((i for i, uid in enumerate(player.defense) if uid is not None), None)
            if attack_slot is None or defense_slot is None:
                return
            player.attack[attack_slot], player.defense[defense_slot] = player.defense[defense_slot], player.attack[attack_slot]
            return
        if action == "increase_faith_per_opponent_saints":
            target_bonus = max(0, int(effect.amount))
            count = len(engine.all_saints_on_field(1 - owner_idx))
            for t_uid in targets:
                inst = engine.state.instances[t_uid]
                inst.current_faith = (inst.current_faith or 0) + (count * target_bonus)
            return
        if action == "increase_faith_if_damaged":
            amount = max(0, int(effect.amount))
            for t_uid in targets:
                inst = engine.state.instances[t_uid]
                base_faith = inst.definition.faith or 0
                current_faith = inst.current_faith if inst.current_faith is not None else base_faith
                if current_faith < base_faith:
                    inst.current_faith = current_faith + amount
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
        event_card_uid = str(payload.get("card", payload.get("saint", payload.get("token", ""))))

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

        target_uid = str(payload.get("card", ""))
        if target_uid and target_uid in ctx.engine.state.instances:
            target_inst = ctx.engine.state.instances[target_uid]
            current_faith = target_inst.current_faith if target_inst.current_faith is not None else (target_inst.definition.faith or 0)
        else:
            target_inst = None
            current_faith = None

        target_current_faith_gte = condition.get("target_current_faith_gte")
        if target_current_faith_gte is not None:
            if current_faith is None or current_faith < int(target_current_faith_gte):
                return False

        controller_has_name = condition.get("controller_has_saint_with_name")
        if controller_has_name:
            wanted = _norm(str(controller_has_name))
            if not any(
                _norm(ctx.engine.state.instances[uid].definition.name) == wanted
                for uid in ctx.engine.all_saints_on_field(owner_idx)
            ):
                return False

        hand_name = condition.get("controller_has_card_in_hand_with_name")
        if hand_name:
            wanted = _norm(str(hand_name))
            if not any(_norm(ctx.engine.state.instances[uid].definition.name) == wanted for uid in ctx.engine.state.players[owner_idx].hand):
                return False
        event_name_is = condition.get("event_card_name_is")
        if event_name_is and event_card_uid:
            wanted = _norm(str(event_name_is))
            inst = ctx.engine.state.instances.get(event_card_uid)
            if inst is None or _norm(inst.definition.name) != wanted:
                return False
        target_is_damaged = condition.get("target_is_damaged")
        if target_is_damaged:
            if target_inst is None:
                return False
            if (current_faith or 0) >= (target_inst.definition.faith or 0):
                return False
        deck_name = condition.get("controller_has_card_in_deck_with_name")
        if deck_name:
            wanted = _norm(str(deck_name))
            if not any(_norm(ctx.engine.state.instances[uid].definition.name) == wanted for uid in ctx.engine.state.players[owner_idx].deck):
                return False
        distinct_saints_gte = condition.get("controller_has_distinct_saints_gte")
        if distinct_saints_gte is not None:
            names = {
                _norm(ctx.engine.state.instances[uid].definition.name)
                for uid in ctx.engine.all_saints_on_field(owner_idx)
            }
            if len(names) < int(distinct_saints_gte):
                return False
        selected_target = _norm(str(ctx.engine.state.flags.get("_runtime_selected_target", "")))
        selected_target_in = condition.get("selected_target_in")
        if selected_target_in:
            allowed = {_norm(v) for v in selected_target_in}
            if selected_target not in allowed:
                return False
        selected_target_startswith = condition.get("selected_target_startswith")
        if selected_target_startswith:
            prefix = _norm(str(selected_target_startswith))
            if not selected_target.startswith(prefix):
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
