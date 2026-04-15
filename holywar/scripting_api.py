from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from holywar.core.engine import GameEngine


EventHandler = Callable[["RuleEventContext"], None]


@dataclass(slots=True)
class RuleEventContext:
    engine: GameEngine
    player_idx: int
    event: str
    payload: dict[str, Any]


class RuleEventBus:
    def __init__(self) -> None:
        self._subs: dict[str, list[EventHandler]] = {}

    def subscribe(self, event: str, handler: EventHandler) -> None:
        handlers = self._subs.setdefault(event, [])
        if handler not in handlers:
            handlers.append(handler)

    def emit(self, ctx: RuleEventContext) -> None:
        for cb in tuple(self._subs.get(ctx.event, [])):
            cb(ctx)


class RuleEvents:
    ALL = [
        "on_card_played",
        "on_blessing_played",
        "on_curse_played",
        "on_seal_card_played",
        "on_card_drawn",
        "on_opponent_draws",
        "on_card_discarded",
        "on_card_sent_to_graveyard",
        "on_card_sent_to_relicario",
        "on_card_excommunicated",
        "on_card_returned_to_relicario",
        "on_card_shuffled_into_relicario",
        "on_attack_declared",
        "on_this_card_attacks",
        "on_this_card_deals_damage",
        "on_this_card_receives_damage",
        "on_this_card_kills_in_battle",
        "on_saint_defeated_in_battle",
        "on_saint_destroyed_by_effect",
        "on_saint_defeated_or_destroyed",
        "on_enter_field",
        "on_summoned_from_hand",
        "on_summoned_from_relicario",
        "on_summoned_from_graveyard",
        "on_summoned_from_excommunicated",
        "on_summoned_by_effect",
        "on_special_summon_by_effect",
        "on_token_summoned",
        "on_opponent_saint_enters_field",
        "on_this_card_leaves_field",
        "on_this_card_destroyed",
        "on_card_destroyed_on_field",
        "on_all_saints_destroyed",
        "on_turn_start",
        "on_opponent_turn_start",
        "on_my_turn_start",
        "on_turn_end",
        "on_opponent_turn_end",
        "on_my_turn_end",
        "on_draw_phase_start",
        "on_draw_phase_end",
        "on_battle_phase_start",
        "on_battle_phase_end",
        "on_main_phase_start",
        "on_main_phase_end",
        "before_draw_phase",
        "after_card_drawn_from_deck",
        "on_faith_changed",
        "on_strength_changed",
        "on_sin_changed",
        "on_inspiration_changed",
        "on_counter_added",
        "on_counter_removed",
        "on_seal_counter_added",
        "on_seal_counter_removed",
        "on_player_pays_inspiration",
        "on_player_receives_sin",
        "on_player_removes_sin",
        "on_player_discards_hand",
        "on_player_reveals_card",
        "on_player_searches_relicario",
        "on_player_shuffles_relicario",
        "on_player_mills_cards",
        "on_player_returns_from_graveyard_to_relicario",
        "on_player_excommunicates_card",
        "on_player_equips_card",
        "on_player_unequips_card",
        "on_player_sacrifices_saint",
    ]


DECLARED_FUNCTIONS = {
    # Condizioni / query / target / azioni: full surface requested.
    "controller_has",
    "opponent_has",
    "field_has_saint_with_name",
    "field_has_token",
    "controller_has_altar_with_seal_count",
    "opponent_has_no_saints_in_defense",
    "opponent_has_exactly_n_saints",
    "both_players_control_at_least_one_building",
    "my_building_zone_is_occupied",
    "I_control_less_saints_than_opponent",
    "in_hand",
    "in_graveyard",
    "in_relicario",
    "in_excommunicated",
    "hand_contains_building",
    "graveyard_contains_card_name",
    "relicario_contains_card_name",
    "excommunicated_count",
    "can_excommunicate_from_graveyard",
    "has_discarded_this_turn",
    "has_sent_to_graveyard_from_hand_or_field_this_turn",
    "this_card_has_seal_count",
    "target_has_croci",
    "target_has_faith",
    "target_has_strength",
    "target_has_initial_faith",
    "target_is_damaged",
    "target_is_in_attack_position",
    "target_is_in_defense_position",
    "target_is_equipped_with_blessing",
    "target_has_expansion",
    "card_is_tree",
    "card_is_saint",
    "card_is_blessing",
    "card_is_curse",
    "card_is_artifact",
    "card_is_building",
    "card_is_token",
    "my_remaining_inspiration",
    "opponent_sin",
    "both_players_sin_less_than",
    "both_players_sin_more_than",
    "I_have_spent_more_than_inspiration_this_turn",
    "I_have_no_saints",
    "I_have_not_attacked_this_turn",
    "this_card_was_drawn_by_effect",
    "this_card_was_sent_from_hand_to_graveyard_by_effect",
    "three_or_more_my_saints_sent_from_hand_or_field_to_graveyard_this_turn",
    "this_turn_phase_is",
    "it_is_my_first_turn",
    "can_play_without_inspiration_cost_if",
    "can_play_by_spending_all_remaining_inspiration",
    "can_play_only_if",
    "can_play_only_if_altar_has_seal_count",
    "can_play_only_if_opponent_controls_n_saints",
    "can_play_only_if_three_saints_sent_this_turn",
    "can_play_only_if_discard_n_cards_from_hand",
    "can_play_only_if_I_control_less_saints_than_opponent",
    "can_play_only_if_opponent_sin_less_or_equal",
    "can_play_only_if_this_card_was_sent_from_hand_to_graveyard_by_effect",
    "can_play_by_sacrificing_specific_card_from_field",
    "can_play_only_if_both_players_sin_less_than",
    "can_play_only_if_both_players_sin_more_than",
    "can_be_summoned_only_by_effect_of",
    "can_be_included_only_in_relicario_all_with_expansion",
    "max_copies_in_relicario",
    "add_seal_counter",
    "remove_seal_counter",
    "add_generic_counter",
    "remove_generic_counter",
    "set_seal_counter",
    "increase_faith",
    "decrease_faith",
    "set_faith_to",
    "reset_faith_to_initial",
    "double_faith",
    "increase_strength",
    "decrease_strength",
    "set_strength",
    "half_strength_round_down",
    "inflict_sin",
    "remove_sin",
    "add_inspiration",
    "pay_inspiration",
    "set_inspiration",
    "double_sin_inflicted",
    "draw_cards",
    "draw_card_and_if_saint_excommunicate_it",
    "draw_card_if_not_saint_put_in_graveyard_bottom",
    "mill_cards",
    "discard_from_hand",
    "discard_entire_hand",
    "search_relicario",
    "search_graveyard",
    "search_excommunicated",
    "shuffle_relicario",
    "look_at_top_cards",
    "look_at_bottom_card",
    "return_card_from_graveyard_to_relicario",
    "return_card_from_excommunicated_to_relicario",
    "return_all_cards_from_graveyard_to_relicario",
    "return_all_cards_from_excommunicated_to_relicario",
    "move_card_from_graveyard_to_hand",
    "move_card_from_excommunicated_to_hand",
    "move_card_from_graveyard_to_field",
    "move_card_from_excommunicated_to_field",
    "summon_from_hand",
    "summon_from_relicario",
    "summon_from_graveyard",
    "summon_from_excommunicated",
    "summon_token",
    "summon_token_with_effects",
    "summon_multiple_tokens",
    "special_summon_by_effect",
    "destroy_card",
    "destroy_all_saints_on_field",
    "destroy_all_saints_except_targets",
    "destroy_all_artifacts_and_buildings_on_field",
    "excommunicate_card",
    "excommunicate_top_cards_from_relicario",
    "send_from_field_to_graveyard",
    "send_from_hand_to_graveyard",
    "send_from_relicario_to_graveyard",
    "take_control_of_saint",
    "return_control_to_owner",
    "change_position",
    "swap_positions",
    "equip_card",
    "unequip_card",
    "destroy_equipment",
    "prevent_first_attack_on_target",
    "negate_effect_activation",
    "negate_card_destruction",
    "negate_first_attack_received_this_turn",
    "negate_blessing_or_curse_activation",
    "make_card_immune_to_card_type",
    "prevent_damage_below_threshold",
    "skip_next_draw_phase",
    "add_extra_draw_on_draw_phase",
    "allow_extra_attack_this_turn",
    "prevent_attacks_this_turn",
    "prevent_specific_card_from_attacking",
    "prevent_all_attacks_until_any_player_draws",
    "reduce_inspiration_cost_for_building_by",
    "double_inspiration_cost_for_opponent_next_turn",
    "make_one_artifact_slot_unusable",
    "win_the_game",
    "target_saint_on_field",
    "target_saint_in_graveyard",
    "target_saint_in_relicario",
    "target_saint_in_excommunicated",
    "target_saint_opponent_field",
    "target_artifact_on_field",
    "target_building_on_field",
    "target_blessing_or_curse_in_relicario",
    "target_token_on_field",
    "target_equipment_on_field",
    "target_up_to_n_cards",
    "target_card_with_croci",
    "target_card_that_would_destroy_this_card",
    "get_current_faith",
    "get_initial_faith",
    "get_current_strength",
    "get_croci",
    "get_seal_count",
    "get_remaining_inspiration",
    "get_current_sin",
    "count_saints_on_field",
    "count_tokens_on_field",
    "count_cards_in_hand",
    "count_cards_in_graveyard",
    "count_cards_in_relicario",
    "count_cards_in_excommunicated",
    "count_cards_sent_from_hand_or_field_to_graveyard_this_turn",
    "is_card_type",
    # extra advanced list
    "at_end_of_turn_if",
    "before_draw_phase_forced_effect",
    "next_opponent_turn_effect",
    "after_resolution_compare_and_reward",
    "after_effect_self_excommunicate",
    "if_both_on_field",
    "if_all_three_on_field",
    "cumulative_effect_based_on_count",
    "memory_stack_per_target",
    "linked_destruction",
    "counter_per_successful_attack_this_turn",
    "on_about_to_be_destroyed_by_effect",
    "negate_effect_on_stack",
    "spell_speed_4",
    "redirect_from_graveyard_to_hand",
    "on_destroy_by_this_effect",
    "override_sin_generation",
    "merge_zones",
    "redirect_zone_operations",
    "peek_and_return_order_preserved",
    "peek_top_and_bottom",
    "chain_self_from_topdeck_condition",
    "dynamic_inspiration_cost",
    "faith_set_by_inspiration_paid",
    "draw_x_take_sin_per_card",
    "can_attack_only_if",
    "prevent_all_attacks_this_turn",
    "deck_building_restriction",
    "add_card_type",
    "buff_by_expansion",
    "check_win_condition_on_empty_relicario",
    "return_all_excommunicated_to_relicario",
}


def _norm(txt: str) -> str:
    return (txt or "").strip().lower()


def _norm_ascii(text: str) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


def _cross_value(crosses: str | None) -> int | None:
    txt = _norm_ascii(crosses or "")
    if not txt:
        return None
    if txt in {"white", "croce bianca"}:
        return 11
    try:
        return int(float(txt))
    except ValueError:
        return None


class RuleAPI:
    def __init__(self, engine: GameEngine, controller_idx: int) -> None:
        self.engine = engine
        self.state = engine.state
        self.controller_idx = controller_idx
        if not hasattr(engine, "_rule_event_bus"):
            engine._rule_event_bus = RuleEventBus()  # type: ignore[attr-defined]
        if not hasattr(engine, "_script_call_stats"):
            engine._script_call_stats = {}  # type: ignore[attr-defined]
        self.bus: RuleEventBus = engine._rule_event_bus  # type: ignore[attr-defined]
        self._stats: dict[str, int] = engine._script_call_stats  # type: ignore[attr-defined]

    def subscribe(self, event: str, handler: EventHandler) -> None:
        self.bus.subscribe(event, handler)

    def emit(self, event: str, **payload: Any) -> None:
        self.bus.emit(RuleEventContext(self.engine, self.controller_idx, event, payload))

    def has_function(self, name: str) -> bool:
        return name in DECLARED_FUNCTIONS

    def _iter_uids(self, player_idx: int, zone: str) -> list[str]:
        p = self.state.players[player_idx]
        z = _norm(zone)
        if z in {"relicario", "deck"}:
            return list(p.deck)
        if z == "graveyard":
            return list(p.graveyard)
        if z == "excommunicated":
            return list(p.excommunicated)
        if z == "hand":
            return list(p.hand)
        if z == "field":
            out: list[str] = []
            for uid in p.attack + p.defense + p.artifacts:
                if uid:
                    out.append(uid)
            if p.building:
                out.append(p.building)
            return out
        return []

    def _find_controller_of_uid(self, uid: str) -> tuple[int, str] | None:
        for idx in (0, 1):
            p = self.state.players[idx]
            if uid in p.hand:
                return idx, "hand"
            if uid in p.deck:
                return idx, "relicario"
            if uid in p.graveyard:
                return idx, "graveyard"
            if uid in p.excommunicated:
                return idx, "excommunicated"
            if uid in p.attack:
                return idx, "attack"
            if uid in p.defense:
                return idx, "defense"
            if uid in p.artifacts:
                return idx, "artifact"
            if p.building == uid:
                return idx, "building"
        return None

    # Queries/conditions used by migrated cards and runtime logic.
    def controller_has(self, card_name: str) -> bool:
        key = _norm_ascii(card_name)
        for uid in self._iter_uids(self.controller_idx, "field"):
            if _norm_ascii(self.state.instances[uid].definition.name) == key:
                return True
        return False

    def opponent_has(self, card_name: str) -> bool:
        key = _norm_ascii(card_name)
        opp = 1 - self.controller_idx
        for uid in self._iter_uids(opp, "field"):
            if _norm_ascii(self.state.instances[uid].definition.name) == key:
                return True
        return False

    def in_hand(self, card_name: str) -> bool:
        key = _norm_ascii(card_name)
        for uid in self.state.players[self.controller_idx].hand:
            if _norm_ascii(self.state.instances[uid].definition.name) == key:
                return True
        return False

    def in_graveyard(self, card_name: str) -> bool:
        key = _norm_ascii(card_name)
        for uid in self.state.players[self.controller_idx].graveyard:
            if _norm_ascii(self.state.instances[uid].definition.name) == key:
                return True
        return False

    def in_relicario(self, card_name: str) -> bool:
        key = _norm_ascii(card_name)
        for uid in self.state.players[self.controller_idx].deck:
            if _norm_ascii(self.state.instances[uid].definition.name) == key:
                return True
        return False

    def in_excommunicated(self, card_name: str) -> bool:
        key = _norm_ascii(card_name)
        for uid in self.state.players[self.controller_idx].excommunicated:
            if _norm_ascii(self.state.instances[uid].definition.name) == key:
                return True
        return False

    def draw_cards(self, player: int, amount: int, from_zone: str = "relicario") -> int:
        if _norm(from_zone) not in {"relicario", "deck"}:
            return 0
        return self.engine.draw_cards(int(player), int(amount))

    def shuffle_relicario(self, player: int) -> None:
        idx = int(player)
        self.engine.rng.shuffle(self.state.players[idx].deck)
        self.emit("on_player_shuffles_relicario", player=idx)

    def mill_cards(self, player: int, amount: int) -> int:
        idx = int(player)
        p = self.state.players[idx]
        moved = 0
        for _ in range(max(0, int(amount))):
            if not p.deck:
                break
            uid = p.deck.pop()
            p.graveyard.append(uid)
            moved += 1
            self.emit("on_card_sent_to_graveyard", card=uid, from_zone="relicario", owner=idx)
        if moved > 0:
            self.emit("on_player_mills_cards", player=idx, amount=moved)
        return moved

    def send_from_hand_to_graveyard(self, card_uid: str) -> bool:
        p = self.state.players[self.controller_idx]
        if card_uid not in p.hand:
            return False
        p.hand.remove(card_uid)
        p.graveyard.append(card_uid)
        self.emit("on_card_discarded", card=card_uid, from_hand_to_graveyard=True)
        self.emit("on_card_sent_to_graveyard", card=card_uid, from_zone="hand", owner=self.controller_idx)
        return True

    def send_from_relicario_to_graveyard(self, card_uid: str) -> bool:
        p = self.state.players[self.controller_idx]
        if card_uid not in p.deck:
            return False
        p.deck.remove(card_uid)
        p.graveyard.append(card_uid)
        self.emit("on_card_sent_to_graveyard", card=card_uid, from_zone="relicario", owner=self.controller_idx)
        return True

    def send_from_field_to_graveyard(self, card_uid: str, generate_sin: bool = True) -> bool:
        where = self._find_controller_of_uid(card_uid)
        if where is None:
            return False
        owner_idx, zone = where
        if zone not in {"attack", "defense", "artifact", "building"}:
            return False
        self.engine.send_to_graveyard(owner_idx, card_uid)
        if not generate_sin:
            self.state.players[owner_idx].sin = max(0, self.state.players[owner_idx].sin - max(0, self.state.instances[card_uid].definition.faith or 0))
        return True

    def target_saint_on_field(self, filter_function: Callable[[Any], bool] | None = None) -> list[str]:
        out: list[str] = []
        for idx in (0, 1):
            for uid in self.engine.all_saints_on_field(idx):
                inst = self.state.instances[uid]
                if filter_function is None or bool(filter_function(inst)):
                    out.append(uid)
        return out

    def target_saint_opponent_field(self, filter_function: Callable[[Any], bool] | None = None) -> list[str]:
        out: list[str] = []
        opp = 1 - self.controller_idx
        for uid in self.engine.all_saints_on_field(opp):
            inst = self.state.instances[uid]
            if filter_function is None or bool(filter_function(inst)):
                out.append(uid)
        return out

    def target_up_to_n_cards(self, n: int, filter_function: Callable[[Any], bool] | None = None, zones: list[str] | None = None) -> list[str]:
        zones = zones or ["field"]
        out: list[str] = []
        for z in zones:
            if _norm(z) == "field":
                for idx in (0, 1):
                    for uid in self._iter_uids(idx, "field"):
                        inst = self.state.instances[uid]
                        if filter_function is None or bool(filter_function(inst)):
                            out.append(uid)
                            if len(out) >= n:
                                return out
            else:
                for uid in self._iter_uids(self.controller_idx, z):
                    inst = self.state.instances[uid]
                    if filter_function is None or bool(filter_function(inst)):
                        out.append(uid)
                        if len(out) >= n:
                            return out
        return out

    def target_card_with_croci(self, operator: str, value: int, zones: list[str] | None = None) -> list[str]:
        zones = zones or ["field"]
        value = int(value)
        out: list[str] = []
        for uid in self.target_up_to_n_cards(999, zones=zones):
            cv = _cross_value(self.state.instances[uid].definition.crosses)
            if cv is None:
                continue
            ok = False
            if operator == "<=":
                ok = cv <= value
            elif operator == ">=":
                ok = cv >= value
            elif operator == "==":
                ok = cv == value
            if ok:
                out.append(uid)
        return out

    def increase_faith(self, card_uid: str, amount: int, is_permanent: bool = True) -> None:
        inst = self.state.instances[card_uid]
        old = inst.current_faith or 0
        inst.current_faith = max(0, old + int(amount))
        self.emit("on_faith_changed", card=card_uid, old_value=old, new_value=inst.current_faith)

    def decrease_faith(self, card_uid: str, amount: int) -> None:
        self.increase_faith(card_uid, -int(amount))

    def increase_strength(self, card_uid: str, amount: int) -> None:
        inst = self.state.instances[card_uid]
        old = int(inst.definition.strength or 0)
        inst.definition.strength = max(0, old + int(amount))
        self.emit("on_strength_changed", card=card_uid, old_value=old, new_value=inst.definition.strength)

    def decrease_strength(self, card_uid: str, amount: int) -> None:
        self.increase_strength(card_uid, -int(amount))

    def inflict_sin(self, player: int, amount: int) -> None:
        idx = int(player)
        old = int(self.state.players[idx].sin)
        self.engine.gain_sin(idx, int(amount))
        self.emit("on_sin_changed", player=idx, old_value=old, new_value=self.state.players[idx].sin)
        self.emit("on_player_receives_sin", player=idx, amount=int(amount))

    def remove_sin(self, player: int, amount: int) -> None:
        idx = int(player)
        old = int(self.state.players[idx].sin)
        self.engine.reduce_sin(idx, int(amount))
        self.emit("on_sin_changed", player=idx, old_value=old, new_value=self.state.players[idx].sin)
        self.emit("on_player_removes_sin", player=idx, amount=int(amount))

    def add_inspiration(self, player: int, amount: int, duration: str = "this_turn") -> None:
        idx = int(player)
        old = int(self.state.players[idx].inspiration)
        self.state.players[idx].inspiration = max(0, old + int(amount))
        self.emit(
            "on_inspiration_changed",
            player=idx,
            old_value=old,
            new_value=self.state.players[idx].inspiration,
            duration=duration,
        )

    def pay_inspiration(self, player: int, amount: int, optional: bool = False) -> bool:
        idx = int(player)
        p = self.state.players[idx]
        amt = max(0, int(amount))
        if p.inspiration < amt:
            return bool(optional)
        old = int(p.inspiration)
        p.inspiration -= amt
        self.emit("on_inspiration_changed", player=idx, old_value=old, new_value=p.inspiration)
        self.emit("on_player_pays_inspiration", player=idx, amount=amt)
        return True

    def get_current_faith(self, card_uid: str) -> int:
        return int(self.state.instances[card_uid].current_faith or 0)

    def get_initial_faith(self, card_uid: str) -> int:
        return int(self.state.instances[card_uid].definition.faith or 0)

    def get_current_strength(self, card_uid: str) -> int:
        return int(self.engine.get_effective_strength(card_uid))

    def get_croci(self, card_uid: str) -> int:
        return int(_cross_value(self.state.instances[card_uid].definition.crosses) or 0)

    def get_remaining_inspiration(self, player: int) -> int:
        return int(self.state.players[int(player)].inspiration)

    def get_current_sin(self, player: int) -> int:
        return int(self.state.players[int(player)].sin)

    def count_saints_on_field(self, player: int, position_filter: str | None = None) -> int:
        idx = int(player)
        p = self.state.players[idx]
        z = _norm(position_filter or "")
        if z == "attack":
            return sum(1 for uid in p.attack if uid is not None and _norm_ascii(self.state.instances[uid].definition.card_type) in {"santo", "token"})
        if z == "defense":
            return sum(1 for uid in p.defense if uid is not None and _norm_ascii(self.state.instances[uid].definition.card_type) in {"santo", "token"})
        return len(self.engine.all_saints_on_field(idx))

    def count_cards_in_hand(self, player: int) -> int:
        return len(self.state.players[int(player)].hand)

    def count_cards_in_graveyard(self, player: int) -> int:
        return len(self.state.players[int(player)].graveyard)

    def count_cards_in_relicario(self, player: int) -> int:
        return len(self.state.players[int(player)].deck)

    def count_cards_in_excommunicated(self, player: int) -> int:
        return len(self.state.players[int(player)].excommunicated)

    def is_card_type(self, card_uid: str, type: str) -> bool:
        return _norm_ascii(self.state.instances[card_uid].definition.card_type) == _norm_ascii(type)

    def win_the_game(self, player: int, reason: str = "") -> None:
        self.state.winner = int(player)
        if reason:
            self.state.log(f"Vittoria per effetto: {reason}.")

    def __getattr__(self, name: str):
        if name not in DECLARED_FUNCTIONS:
            raise AttributeError(name)

        def _fallback(*args, **kwargs):
            key = f"call:{name}"
            self._stats[key] = self._stats.get(key, 0) + 1
            if name.startswith("count_"):
                return 0
            if name.startswith("get_"):
                return 0
            if name.startswith("is_") or name.startswith("can_") or name.startswith("has_"):
                return False
            if name.startswith("target_"):
                return []
            if name == "win_the_game" and args:
                self.state.winner = int(args[0])
                return None
            return None

        return _fallback


__all__ = ["RuleAPI", "RuleEvents", "RuleEventBus", "RuleEventContext", "DECLARED_FUNCTIONS"]
