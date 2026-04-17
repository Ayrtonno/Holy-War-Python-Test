from __future__ import annotations

import random
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from holywar.core.state import (
    ARTIFACT_SLOTS,
    DEFENSE_SLOTS,
    MAX_HAND,
    TURN_INSPIRATION,
    ATTACK_SLOTS,
    CardInstance,
    GameState,
    PlayerState,
)
from holywar.data.deck_builder import build_premade_deck, build_test_deck
from holywar.data.models import CardDefinition
from holywar.effects.library import resolve_activated_effect, resolve_card_effect, resolve_enter_effect
from holywar.effects.runtime import EffectSpec, runtime_cards
from holywar.effects.state_flags import ensure_runtime_state, refresh_player_flags, set_phase
from holywar.scripting_api import RuleAPI


SAINT_TYPES = {"santo", "token"}
QUICK_TYPES = {"benedizione", "maledizione"}


@dataclass(slots=True)
class ActionResult:
    ok: bool
    message: str


def _norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", text)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


class GameEngine:
    def __init__(self, state: GameState, seed: int | None = None):
        self.state = state
        self.rng = random.Random(seed)
        self._bootstrap_runtime_bindings()
        ensure_runtime_state(self)
        refresh_player_flags(self)

    def _bootstrap_runtime_bindings(self) -> None:
        runtime_cards.ensure_all_cards_migrated(self)
        for controller_idx in (0, 1):
            player = self.state.players[controller_idx]
            for uid in player.attack + player.defense + player.artifacts:
                if uid is not None:
                    runtime_cards.on_enter_bind_triggers(self, controller_idx, uid)
            if player.building is not None:
                runtime_cards.on_enter_bind_triggers(self, controller_idx, player.building)

    def rules_api(self, controller_idx: int) -> RuleAPI:
        return RuleAPI(self, controller_idx)
    
    def _reset_card_runtime_state(self, uid: str) -> None:
        if uid not in self.state.instances:
            return
        inst = self.state.instances[uid]

        # Ripristina Fede iniziale stampata sulla carta
        inst.current_faith = inst.definition.faith if inst.definition.faith is not None else None

        # Rimuove ogni buff/debuff/marker runtime
        inst.blessed = []
        inst.cursed = []

        # La carta fuori dal campo non deve conservare stati di utilizzo
        inst.exhausted = False

    def _emit_event(self, event: str, actor_idx: int, **payload) -> None:
        self.rules_api(actor_idx).emit(event, actor_idx=actor_idx, **payload)
        # Alias English/Italian spellings used by scripted effects.
        if "relicario" in event:
            self.rules_api(actor_idx).emit(event.replace("relicario", "reliquiary"), actor_idx=actor_idx, **payload)
        elif "reliquiary" in event:
            self.rules_api(actor_idx).emit(event.replace("reliquiary", "relicario"), actor_idx=actor_idx, **payload)

    def _locate_uid_zone(self, owner_idx: int, uid: str) -> str:
        player = self.state.players[owner_idx]
        if uid in player.hand:
            return "hand"
        if uid in player.deck:
            return "relicario"
        if uid in player.graveyard:
            return "graveyard"
        if uid in player.excommunicated:
            return "excommunicated"
        if uid in player.attack:
            return "attack"
        if uid in player.defense:
            return "defense"
        if uid in player.artifacts:
            return "artifact"
        if player.building == uid:
            return "building"
        return "unknown"

    @staticmethod
    def create_new(
        cards: list[CardDefinition],
        p1_name: str,
        p2_name: str,
        p1_expansion: str,
        p2_expansion: str,
        p1_premade_deck_id: str | None = None,
        p2_premade_deck_id: str | None = None,
        seed: int | None = None,
    ) -> "GameEngine":
        rng = random.Random(seed)
        instance_counter = 0
        instances: dict[str, CardInstance] = {}

        def make_uid() -> str:
            nonlocal instance_counter
            instance_counter += 1
            return f"c{instance_counter:05d}"

        def copy_card(card_def: CardDefinition, owner: int) -> str:
            uid = make_uid()
            card_copy = CardDefinition.from_dict(card_def.to_dict())
            faith_value = card_copy.faith if card_copy.faith is not None else None
            instances[uid] = CardInstance(
                uid=uid,
                definition=card_copy,
                owner=owner,
                current_faith=faith_value,
            )
            return uid

        deck_warnings: list[str] = []

        def build_decks(owner: int, expansion: str, premade_deck_id: str | None) -> tuple[list[str], list[str]]:
            if premade_deck_id:
                premade = build_premade_deck(cards, premade_deck_id)
                built = premade.deck
                deck_warnings.extend(premade.warnings)
            else:
                built = build_test_deck(cards, expansion)
            deck: list[str] = []
            white: list[str] = []
            for cdef in built.main_deck:
                deck.append(copy_card(cdef, owner))
            for cdef in built.white_deck:
                white.append(copy_card(cdef, owner))
            rng.shuffle(deck)
            rng.shuffle(white)
            return deck, white

        p1_deck, p1_white = build_decks(0, p1_expansion, p1_premade_deck_id)
        p2_deck, p2_white = build_decks(1, p2_expansion, p2_premade_deck_id)

        p1 = PlayerState.empty(p1_name)
        p1.deck = p1_deck
        p1.white_deck = p1_white
        p2 = PlayerState.empty(p2_name)
        p2.deck = p2_deck
        p2.white_deck = p2_white
        state = GameState(
            players=[p1, p2],
            instances=instances,
            active_player=0,
            turn_number=0,
            phase="preparation",
            preparation_turns_done=0,
            flags={
                "attack_count": {"0": 0, "1": 0},
                "spore_pending": {"0": False, "1": False},
                "double_cost_turns": {"0": 0, "1": 0},
                "saga_bonus": {"0": 0, "1": 0},
                "activated_turn": {},
                "attack_shield_turn": {},
                "spent_inspiration_turn": {"0": 0, "1": 0},
                "bonus_inspiration_next_turn": {"0": 0, "1": 0},
                "counter_spell_ready": {"0": 0, "1": 0},
                "cards_drawn_this_turn": {"0": [], "1": []},
            },
        )
        engine = GameEngine(state, seed=seed)
        runtime_cards.ensure_all_cards_migrated(engine)
        engine.initial_setup_draw()
        for w in deck_warnings:
            engine.state.log(f"[WARN DECK] {w}")
        return engine

    def initial_setup_draw(self) -> None:
        for idx in (0, 1):
            self.draw_cards(idx, 5)
        self.state.flags.setdefault("cards_drawn_this_turn", {"0": [], "1": []})["0"] = []
        self.state.flags.setdefault("cards_drawn_this_turn", {"0": [], "1": []})["1"] = []
        self.state.log("Setup iniziale completato: entrambi i giocatori hanno pescato 5 carte.")

    def draw_cards(self, player_idx: int, amount: int) -> int:
        player = self.state.players[player_idx]
        drawn = 0
        for _ in range(amount):
            if len(player.hand) >= MAX_HAND:
                break
            if not player.deck:
                break
            drawn_uid = player.deck.pop()
            player.hand.append(drawn_uid)
            drawn += 1
            self.state.flags.setdefault("cards_drawn_this_turn", {"0": [], "1": []}).setdefault(str(player_idx), []).append(drawn_uid)
            self._emit_event("on_card_drawn", player_idx, card=drawn_uid, from_zone="relicario")
            card_name = self.state.instances[drawn_uid].definition.name
            if runtime_cards.get_auto_play_on_draw(card_name):
                flags = self.state.flags
                previous_source = flags.get("_runtime_source_card")
                previous_selected = flags.get("_runtime_selected_target")
                flags["_runtime_source_card"] = drawn_uid
                flags["_runtime_selected_target"] = ""
                try:
                    runtime_cards._apply_effect(self, player_idx, drawn_uid, [drawn_uid], EffectSpec(action="move_source_to_board"))
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
                self.state.flags.setdefault("runtime_state", {})["request_end_turn"] = True
            self._emit_event("after_card_drawn_from_deck", player_idx, card=drawn_uid)
            self._emit_event("on_opponent_draws", 1 - player_idx, card=drawn_uid, opponent=player_idx)
        refresh_player_flags(self)
        return drawn

    def all_saints_on_field(self, player_idx: int) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for board_idx in (0, 1):
            player = self.state.players[board_idx]
            for uid in player.attack + player.defense:
                if uid is None or uid in seen:
                    continue
                inst = self.state.instances.get(uid)
                if inst is None:
                    continue
                if int(inst.owner) != int(player_idx):
                    continue
                ctype = _norm(inst.definition.card_type)
                if ctype in SAINT_TYPES:
                    out.append(uid)
                    seen.add(uid)
        return out

    def all_attack_saints(self, player_idx: int) -> list[str]:
        player = self.state.players[player_idx]
        out: list[str] = []
        for uid in player.attack:
            if uid is None:
                continue
            ctype = _norm(self.state.instances[uid].definition.card_type)
            if ctype in SAINT_TYPES:
                out.append(uid)
        return out

    def _has_artifact(self, player_idx: int, name: str) -> bool:
        return any(
            uid and _norm(self.state.instances[uid].definition.name) == _norm(name)
            for uid in self.state.players[player_idx].artifacts
        )

    def _count_artifact(self, player_idx: int, name: str) -> int:
        return sum(
            1
            for uid in self.state.players[player_idx].artifacts
            if uid and _norm(self.state.instances[uid].definition.name) == _norm(name)
        )

    def _has_building(self, player_idx: int, name: str) -> bool:
        uid = self.state.players[player_idx].building
        if uid is None:
            return False
        return _norm(self.state.instances[uid].definition.name) == _norm(name)

    def _count_pyramids(self, player_idx: int) -> int:
        pyramid_names = {_norm("Piramide: Chefren"), _norm("Piramide: Cheope"), _norm("Piramide: Micerino")}
        return sum(
            1
            for uid in self.state.players[player_idx].artifacts
            if uid and _norm(self.state.instances[uid].definition.name) in pyramid_names
        )

    def _cleanup_zero_faith_saints(self) -> None:
        seen: set[str] = set()
        for board_owner in (0, 1):
            player = self.state.players[board_owner]
            for uid in list(player.attack + player.defense):
                if uid is None or uid in seen or uid not in self.state.instances:
                    continue
                seen.add(uid)
                inst = self.state.instances[uid]
                if _norm(inst.definition.card_type) not in SAINT_TYPES:
                    continue
                faith = inst.current_faith if inst.current_faith is not None else (inst.definition.faith or 0)
                if faith <= 0:
                    self.destroy_saint_by_uid(inst.owner, uid, cause="effect")

    def _find_board_owner_of_uid(self, uid: str) -> int | None:
        for owner_idx in (0, 1):
            player = self.state.players[owner_idx]
            if uid in player.attack or uid in player.defense or uid == player.building:
                return owner_idx
        return None

    def _get_altare_sigilli(self, player_idx: int) -> int:
        uid = self.state.players[player_idx].building
        if uid is None:
            return 0
        inst = self.state.instances[uid]
        if _norm(inst.definition.name) != _norm("Altare dei Sette Sigilli"):
            return 0
        for tag in inst.blessed:
            if tag.startswith("sigilli:"):
                try:
                    return int(tag.split(":", 1)[1])
                except ValueError:
                    return 0
        return 0

    def _set_altare_sigilli(self, player_idx: int, value: int) -> None:
        uid = self.state.players[player_idx].building
        if uid is None:
            return
        inst = self.state.instances[uid]
        if _norm(inst.definition.name) != _norm("Altare dei Sette Sigilli"):
            return
        inst.blessed = [t for t in inst.blessed if not t.startswith("sigilli:")]
        inst.blessed.append(f"sigilli:{max(0, value)}")
        self._refresh_custode_sigilli_bonus(player_idx)

    def _refresh_custode_sigilli_bonus(self, player_idx: int) -> None:
        seals = self._get_altare_sigilli(player_idx)
        level = seals // 6
        if level <= 0:
            return
        for uid in self.all_saints_on_field(player_idx):
            inst = self.state.instances[uid]
            if _norm(inst.definition.name) != _norm("Custode dei Sigilli"):
                continue
            current_level = 0
            keep: list[str] = []
            for tag in inst.blessed:
                if tag.startswith("custode_bonus:"):
                    try:
                        current_level = int(tag.split(":", 1)[1])
                    except ValueError:
                        current_level = 0
                    continue
                keep.append(tag)
            if level > current_level:
                delta = level - current_level
                inst.current_faith = (inst.current_faith or 0) + delta * 3
                keep.extend([f"buff_str:3"] * delta)
                keep.append(f"custode_bonus:{level}")
                inst.blessed = keep
            else:
                keep.append(f"custode_bonus:{current_level}")
                inst.blessed = keep

    def get_effective_strength(self, uid: str) -> int:
        inst = self.state.instances[uid]
        owner = inst.owner
        opponent = 1 - owner
        strength = max(0, inst.definition.strength or 0)
        for tag in inst.blessed:
            if tag.startswith("buff_str:"):
                try:
                    strength += int(tag.split(":", 1)[1])
                except ValueError:
                    pass
        if self._has_artifact(owner, "Járngreipr"):
            strength += 2
        if self._has_artifact(owner, "Gungnir"):
            strength += 1
        for rule in runtime_cards.get_strength_bonus_rules(inst.definition.name):
            artifact_name = str(rule.get("artifact_name", "")).strip()
            if not artifact_name or not self._has_artifact(owner, artifact_name):
                continue
            required_name = str(rule.get("if_card_name", "")).strip()
            if required_name and _norm(inst.definition.name) != _norm(required_name):
                continue
            strength += int(rule.get("self_bonus", 0) or 0)
        if self._count_pyramids(owner) >= 1:
            strength += 5
        sigilli_threshold = runtime_cards.get_sigilli_strength_bonus_threshold(inst.definition.name)
        sigilli_amount = runtime_cards.get_sigilli_strength_bonus_amount(inst.definition.name)
        if sigilli_threshold is not None and sigilli_amount is not None and self._get_altare_sigilli(owner) >= int(sigilli_threshold):
            strength += int(sigilli_amount)
        if self._has_artifact(opponent, "Segno Del Passato"):
            strength -= 4
        return max(0, strength)

    def gain_sin(self, player_idx: int, amount: int) -> None:
        if amount <= 0:
            return
        self.state.players[player_idx].sin += amount
        refresh_player_flags(self)

    def reduce_sin(self, player_idx: int, amount: int) -> None:
        if amount <= 0:
            return
        p = self.state.players[player_idx]
        p.sin = max(0, p.sin - amount)
        refresh_player_flags(self)

    def destroy_saint_by_uid(
        self, owner_idx: int, uid: str, excommunicate: bool = False, cause: str = "effect"
    ) -> None:
        if uid not in self.state.instances:
            return
        inst = self.state.instances[uid]
        board_owner_idx = self._find_board_owner_of_uid(uid)
        if board_owner_idx is None:
            board_owner_idx = owner_idx
        board_player = self.state.players[board_owner_idx]
        if "moribondo_shield" in inst.blessed:
            inst.blessed.remove("moribondo_shield")
            self.state.log(f"Moribondo annulla la distruzione di {inst.definition.name}.")
            return
        if cause == "effect":
            source_uid = str(self.state.flags.get("_runtime_effect_source", ""))
            if source_uid and source_uid in self.state.instances:
                source = self.state.instances[source_uid]
                if (
                    int(source.owner) != int(owner_idx)
                    and _norm(source.definition.card_type) == _norm("artefatto")
                    and self._has_artifact(owner_idx, "Terra")
                ):
                    self.state.log(
                        f"Terra impedisce a {source.definition.name} di distruggere {inst.definition.name}."
                    )
                    return
        if "bende_consacrate" in inst.blessed:
            inst.blessed.remove("bende_consacrate")
            inst.current_faith = 1
            self.state.log(f"Bende Consacrate salva {inst.definition.name}: rimane con 1 Fede.")
            return
        name_key = _norm(inst.definition.name)
        attack_slot = None
        defense_slot = None
        for i, slot_uid in enumerate(board_player.attack):
            if slot_uid == uid:
                attack_slot = i
                break
        if attack_slot is None:
            for i, slot_uid in enumerate(board_player.defense):
                if slot_uid == uid:
                    defense_slot = i
                    break
        from_zone = "attack" if attack_slot is not None else ("defense" if defense_slot is not None else "field")
        if attack_slot is not None:
            board_player.attack[attack_slot] = None
        if defense_slot is not None:
            board_player.defense[defense_slot] = None
        if cause == "battle":
            survival_mode = runtime_cards.get_battle_survival_mode(inst.definition.name)
            if survival_mode == "sacrifice_token_from_field":
                token_name = runtime_cards.get_battle_survival_token_name(inst.definition.name)
                token_uid = None
                if token_name:
                    for s_uid in board_player.attack + board_player.defense:
                        if not s_uid:
                            continue
                        if _norm(self.state.instances[s_uid].definition.name) == _norm(token_name):
                            token_uid = s_uid
                            break
                if token_uid is not None:
                    self.destroy_saint_by_uid(self.state.instances[token_uid].owner, token_uid, cause="effect")
                    inst.current_faith = max(
                        0, runtime_cards.get_battle_survival_restore_faith(inst.definition.name) or (inst.definition.faith or 0)
                    )
                    if attack_slot is not None:
                        board_player.attack[attack_slot] = uid
                    elif defense_slot is not None:
                        board_player.defense[defense_slot] = uid
                    self.state.log(f"{inst.definition.name} evita la distruzione sacrificando {token_name}.")
                    return
            if survival_mode == "excommunicate_card_from_graveyard":
                rescue_names = {_norm(name) for name in runtime_cards.get_battle_survival_names(inst.definition.name)}
                rescue_uid = None
                for g_uid in list(board_player.graveyard):
                    g_name = _norm(self.state.instances[g_uid].definition.name)
                    if g_name in rescue_names:
                        rescue_uid = g_uid
                        break
                if rescue_uid is not None:
                    board_player.graveyard.remove(rescue_uid)
                    board_player.excommunicated.append(rescue_uid)
                    if attack_slot is not None:
                        board_player.attack[attack_slot] = uid
                    elif defense_slot is not None:
                        board_player.defense[defense_slot] = uid
                    inst.current_faith = max(
                        0, runtime_cards.get_battle_survival_restore_faith(inst.definition.name) or (inst.definition.faith or 0)
                    )
                    self.state.log(
                        f"{inst.definition.name} evita la distruzione: scomunica {self.state.instances[rescue_uid].definition.name} "
                        "e annulla la distruzione."
                    )
                    return
        if _norm(inst.definition.card_type) != "token":
            sin_gain = max(0, inst.definition.faith or 0)
            if "no_sin_on_death" in inst.blessed:
                sin_gain = 0
            if self._has_artifact(owner_idx, "Umanit????") and inst.blessed:
                sin_gain = 0
            self.gain_sin(owner_idx, sin_gain)
            self.state.log(
                f"{inst.definition.name} viene distrutto: {self.state.players[owner_idx].name} guadagna {sin_gain} Peccato."
            )
        else:
            self.state.log(f"{inst.definition.name} (Token) viene distrutto.")
        self._emit_event(
            "on_this_card_destroyed",
            owner_idx,
            card=uid,
            by_whom=None,
            reason=cause,
        )
        self._emit_event("on_card_destroyed_on_field", owner_idx, card=uid, by_whom=None, reason=cause)
        if excommunicate:
            self.excommunicate_card(owner_idx, uid, from_zone_override=from_zone)
        else:
            self.send_to_graveyard(owner_idx, uid, token_to_white=True, from_zone_override=from_zone)
        if attack_slot is not None:
            back_uid = board_player.defense[attack_slot]
            if back_uid is not None:
                board_player.attack[attack_slot] = back_uid
                board_player.defense[attack_slot] = None
                self.state.log(
                    f"{self.state.instances[back_uid].definition.name} avanza dalla difesa all'attacco."
                )
        if cause == "battle":
            self._emit_event("on_saint_defeated_in_battle", owner_idx, saint=uid, by_whom=None)
        else:
            self._emit_event("on_saint_destroyed_by_effect", owner_idx, saint=uid, by_whom=None)
        self._emit_event("on_saint_defeated_or_destroyed", owner_idx, saint=uid, reason=cause)

    def start_turn(self) -> None:
        current = self.state.active_player
        player = self.state.players[current]
        runtime_state = ensure_runtime_state(self)
        runtime_state["battle_phase_started"] = False
        set_phase(self, "turn_start")
        self._emit_event("on_turn_start", current, player=current)
        self._emit_event("on_my_turn_start", current, player=current)
        self._emit_event("on_opponent_turn_start", 1 - current, opponent=current)
        set_phase(self, "draw")
        self._emit_event("before_draw_phase", current, player=current)
        self._emit_event("on_draw_phase_start", current, player=current)

        player.inspiration = TURN_INSPIRATION
        bonus_next = self.state.flags.setdefault("bonus_inspiration_next_turn", {"0": 0, "1": 0})
        key = str(self.state.active_player)
        player.inspiration += int(bonus_next.get(key, 0))
        bonus_next[key] = 0
        for uid in player.attack:
            if uid:
                self.state.instances[uid].exhausted = False
        for i, a_uid in enumerate(player.attack):
            if not a_uid:
                continue
            token_name = runtime_cards.get_turn_start_summon_token_name(self.state.instances[a_uid].definition.name)
            if not token_name:
                continue
            def_uid = player.defense[i]
            if def_uid and _norm(self.state.instances[def_uid].definition.name) == _norm(token_name):
                continue
            token_uid = None
            for pool_name in ("white_deck", "deck", "graveyard", "excommunicated"):
                pool = getattr(player, pool_name)
                for c_uid in list(pool):
                    if _norm(self.state.instances[c_uid].definition.name) != _norm(token_name):
                        continue
                    pool.remove(c_uid)
                    token_uid = c_uid
                    break
                if token_uid:
                    break
            if token_uid is not None and player.defense[i] is None:
                player.defense[i] = token_uid
                self.state.log(f"{player.name} evoca {token_name} dietro {self.state.instances[a_uid].definition.name}.")
        self.state.flags.setdefault("attack_count", {"0": 0, "1": 0})[str(self.state.active_player)] = 0
        self.state.flags.setdefault("spent_inspiration_turn", {"0": 0, "1": 0})[str(self.state.active_player)] = 0
        self._cleanup_zero_faith_saints()
        if self.state.phase == "preparation":
            self.state.log(
                f"Preparazione: {player.name} dispone di 10 Ispirazione e non puo attaccare."
            )
            return
        spore_pending = self.state.flags.setdefault("spore_pending", {"0": False, "1": False})
        if spore_pending.get(str(self.state.active_player), False):
            drawn = self.draw_cards(self.state.active_player, 8)
            spore_pending[str(self.state.active_player)] = False
        else:
            bonus_draw = 0
            pyramid_count = sum(
                1
                for uid in player.artifacts
                if uid and _norm(self.state.instances[uid].definition.name) in {
                    _norm("Piramide: Chefren"),
                    _norm("Piramide: Cheope"),
                    _norm("Piramide: Micerino"),
                }
            )
            if pyramid_count >= 3:
                bonus_draw += 2
            drawn = self.draw_cards(self.state.active_player, 3 + bonus_draw)
        self._emit_event("on_draw_phase_end", current, player=current, drawn=drawn)
        set_phase(self, "main")
        self._emit_event("on_main_phase_start", current, player=current)
        self.state.log(f"Turno {self.state.turn_number}: {player.name} pesca {drawn} carte e ottiene 10 Ispirazione.")
        refresh_player_flags(self)

    def end_turn(self) -> None:
        current = self.state.active_player
        runtime_state = ensure_runtime_state(self)
        if bool(runtime_state.get("battle_phase_started", False)):
            set_phase(self, "battle")
            self._emit_event("on_battle_phase_end", current, player=current)
            runtime_state["battle_phase_started"] = False
        set_phase(self, "end")
        self._emit_event("on_main_phase_end", current, player=current)
        self._emit_event("on_turn_end", current, player=current)
        self._emit_event("on_my_turn_end", current, player=current)
        self._emit_event("on_opponent_turn_end", 1 - current, opponent=current)
        self.state.flags.setdefault("cards_drawn_this_turn", {"0": [], "1": []})[str(current)] = []
        self._cleanup_zero_faith_saints()
        self.check_win_conditions()
        if self.state.winner is not None:
            return
        if self.state.phase == "preparation":
            self.state.preparation_turns_done += 1
            if self.state.preparation_turns_done >= 2:
                self.state.phase = "active"
                self.state.coin_toss_winner = self.rng.randint(0, 1)
                self.state.active_player = self.state.coin_toss_winner
                self.state.turn_number = 1
                self.state.log(
                    f"Fine preparazione: lancio moneta -> inizia {self.state.players[self.state.active_player].name}."
                )
                set_phase(self, "setup")
                refresh_player_flags(self)
                self._reset_effect_usage_this_turn()
                self._reset_turn_once_markers_this_turn()
                return
            self.state.active_player = 1 - self.state.active_player
            set_phase(self, "setup")
            refresh_player_flags(self)
            self._reset_effect_usage_this_turn()
            self._reset_turn_once_markers_this_turn()
            return
        double_turns = self.state.flags.setdefault("double_cost_turns", {"0": 0, "1": 0})
        key = str(self.state.active_player)
        if int(double_turns.get(key, 0)) > 0:
            double_turns[key] = int(double_turns[key]) - 1
        self.state.active_player = 1 - self.state.active_player
        self.state.turn_number += 1
        set_phase(self, "setup")
        refresh_player_flags(self)
        self._reset_effect_usage_this_turn()
        self._reset_turn_once_markers_this_turn()

    def card_from_hand(self, player_idx: int, hand_index: int) -> CardInstance | None:
        player = self.state.players[player_idx]
        if hand_index < 0 or hand_index >= len(player.hand):
            return None
        return self.state.instances[player.hand[hand_index]]

    def play_card(self, player_idx: int, hand_index: int, target: str | None = None) -> ActionResult:
        player = self.state.players[player_idx]
        if player_idx != self.state.active_player:
            return ActionResult(False, "Puoi giocare solo nel tuo turno (tranne Benedizioni/Maledizioni in risposta).")
        card = self.card_from_hand(player_idx, hand_index)
        if card is None:
            return ActionResult(False, "Indice mano non valido.")
        ctype = _norm(card.definition.card_type)
        place_owner_idx = player_idx
        zone: str | None = None
        slot = -1
        sacrificed_faith_for_brigante = 0

        # Validate play constraints before spending inspiration or removing card from hand.
        if ctype in SAINT_TYPES:
            if _norm(runtime_cards.get_play_owner(card.definition.name)) in {"opponent", "enemy", "other"}:
                place_owner_idx = 1 - player_idx
            if _norm(card.definition.name) == _norm("Vulcano"):
                return ActionResult(False, "Vulcano puo essere evocato solo tramite Terremoto: Magnitudo 10.")
            if _norm(card.definition.name) == _norm("Brigante"):
                if not self.all_saints_on_field(player_idx):
                    return ActionResult(False, "Per giocare Brigante devi sacrificare un tuo santo sul terreno.")
            zone, slot = self._parse_zone_target(target)
            if zone not in {"attack", "defense"}:
                return ActionResult(False, "Per un Santo/Token indica zona: a1..a3 o d1..d3")
            current = getattr(self.state.players[place_owner_idx], zone)[slot]
            if current is not None:
                return ActionResult(False, "Slot occupato.")
        elif ctype == "artefatto":
            if _norm(card.definition.name) == _norm("Mjolnir"):
                req_idx = next(
                    (
                        i
                        for i, a_uid in enumerate(player.artifacts)
                        if a_uid and _norm(self.state.instances[a_uid].definition.name) == _norm("Járngreipr")
                    ),
                    None,
                )
                if req_idx is None:
                    return ActionResult(False, "Per giocare Mjolnir devi mandare Járngreipr dal terreno al cimitero.")
        elif ctype == "edificio":
            if player.building:
                return ActionResult(False, "Hai gia un Edificio. Va distrutto prima di giocarne un altro.")
            if _norm(card.definition.name) == _norm("Sfinge"):
                needed = {_norm("Piramide: Cheope"), _norm("Piramide: Chefren"), _norm("Piramide: Micerino")}
                present = {
                    _norm(self.state.instances[a_uid].definition.name)
                    for a_uid in player.artifacts
                    if a_uid is not None
                }
                if not needed.issubset(present):
                    return ActionResult(False, "Per giocare Sfinge servono Cheope, Chefren e Micerino sul campo.")

        if ctype not in QUICK_TYPES:
            cost = card.definition.faith or 0
            name_key = _norm(card.definition.name)
            if ctype in SAINT_TYPES:
                if name_key == _norm("Atum"):
                    cost = 0
                if name_key == _norm("Ra"):
                    if any(_norm(self.state.instances[s_uid].definition.name) == _norm("Nun") for s_uid in self.all_saints_on_field(player_idx)):
                        cost = 0
                if name_key == _norm("Impostore") and not any(self.all_saints_on_field(player_idx)):
                    cost = 0
                if name_key == _norm("Geb"):
                    has_building_in_hand = any(
                        _norm(self.state.instances[h_uid].definition.card_type) == "edificio"
                        for i, h_uid in enumerate(player.hand)
                        if i != hand_index
                    )
                    if has_building_in_hand:
                        cost = max(0, cost - 1)
                atum_on_field = any(
                    _norm(self.state.instances[s_uid].definition.name) == _norm("Atum")
                    for s_uid in self.all_saints_on_field(player_idx)
                )
                if atum_on_field and name_key != _norm("Atum"):
                    cost = max(0, (cost + 1) // 2)
            double_turns = self.state.flags.setdefault("double_cost_turns", {"0": 0, "1": 0})
            if int(double_turns.get(str(player_idx), 0)) > 0:
                cost *= 2
            if self._has_building(1 - player_idx, "Sfinge"):
                cost *= 2
            if player.inspiration < cost:
                return ActionResult(False, "Ispirazione insufficiente.")
            player.inspiration -= cost
            spent = self.state.flags.setdefault("spent_inspiration_turn", {"0": 0, "1": 0})
            spent[str(player_idx)] = int(spent.get(str(player_idx), 0)) + cost

        uid = player.hand.pop(hand_index)
        self._emit_event("on_card_played", player_idx, card=uid, card_type=ctype, target=target)
        if ctype == "benedizione":
            self._emit_event("on_blessing_played", player_idx, card=uid, target=target)
        elif ctype == "maledizione":
            self._emit_event("on_curse_played", player_idx, card=uid, target=target)
        if ctype in SAINT_TYPES:
            if _norm(card.definition.name) == _norm("Brigante"):
                own_saints = self.all_saints_on_field(player_idx)
                if own_saints:
                    sacr_uid = own_saints[0]
                    sacr = self.state.instances[sacr_uid]
                    sacrificed_faith_for_brigante = max(0, sacr.definition.faith or 0)
                    sacr.blessed.append("no_sin_on_death")
                    self.destroy_saint_by_uid(self.state.instances[sacr_uid].owner, sacr_uid, cause="effect")
            if zone == "attack":
                self.state.players[place_owner_idx].attack[slot] = uid
            elif zone == "defense":
                self.state.players[place_owner_idx].defense[slot] = uid
            else:
                player.hand.append(uid)
                return ActionResult(False, "Zona non valida per il posizionamento del santo.")
            card.exhausted = False
            if self._count_pyramids(player_idx) >= 2:
                card.current_faith = (card.current_faith or 0) + max(0, card.definition.faith or 0)
            if _norm(card.definition.name) == _norm("Brigante") and sacrificed_faith_for_brigante > 0:
                card.current_faith = (card.current_faith or 0) + sacrificed_faith_for_brigante
                card.blessed.append("no_sin_on_death")
            zone_label = "Attacco" if zone == "attack" else "Difesa"
            self.state.log(f"{player.name} posiziona {card.definition.name} in {zone_label} {slot + 1}.")
            self._emit_event("on_enter_field", player_idx, card=uid, from_zone="hand")
            self._emit_event("on_summoned_from_hand", player_idx, card=uid)
            if _norm(card.definition.card_type) == "token":
                self._emit_event("on_token_summoned", player_idx, token=uid, summoner=player_idx)
            else:
                self._emit_event("on_opponent_saint_enters_field", 1 - player_idx, saint=uid)
            enter_msg = resolve_enter_effect(self, player_idx, uid)
            if enter_msg:
                self.state.log(enter_msg)
            self._refresh_custode_sigilli_bonus(player_idx)
        elif ctype == "artefatto":
            if _norm(card.definition.name) == _norm("Mjolnir"):
                req_idx = next(
                    (
                        i
                        for i, a_uid in enumerate(player.artifacts)
                        if a_uid and _norm(self.state.instances[a_uid].definition.name) == _norm("Járngreipr")
                    ),
                    None,
                )
                if req_idx is None:
                    player.hand.append(uid)
                    return ActionResult(False, "Per giocare Mjolnir devi mandare JÃ¡rngreipr dal terreno al cimitero.")
                req_uid = player.artifacts[req_idx]
                if req_uid:
                    self.send_to_graveyard(player_idx, req_uid)
            blocked = min(ARTIFACT_SLOTS - 1, self._count_artifact(1 - player_idx, "Gggnag'ljep"))
            usable_slots = list(range(ARTIFACT_SLOTS - blocked))
            slot = next((i for i in usable_slots if player.artifacts[i] is None), None)
            if slot is None:
                slot = usable_slots[-1]
                replaced = player.artifacts[slot]
                if replaced:
                    self.send_to_graveyard(player_idx, replaced)
            player.artifacts[slot] = uid
            self.state.log(f"{player.name} posiziona Artefatto {card.definition.name}.")
            self._emit_event("on_enter_field", player_idx, card=uid, from_zone="hand")
            enter_msg = resolve_enter_effect(self, player_idx, uid)
            if enter_msg:
                self.state.log(enter_msg)
        elif ctype == "edificio":
            player.building = uid
            self.state.log(f"{player.name} posiziona Edificio {card.definition.name}.")
            self._emit_event("on_enter_field", player_idx, card=uid, from_zone="hand")
            enter_msg = resolve_enter_effect(self, player_idx, uid)
            if enter_msg:
                self.state.log(enter_msg)
        elif ctype in QUICK_TYPES:
            if self._consume_counter_spell(player_idx):
                self.send_to_graveyard(player_idx, uid)
                self.state.log(f"{player.name} prova a usare {card.definition.name}, ma viene annullata da Barriera Magica.")
                return ActionResult(True, "Attivazione annullata da Barriera Magica.")
            resolved = resolve_card_effect(self, player_idx, uid, target)
            self.send_to_graveyard(player_idx, uid)
            self._cleanup_zero_faith_saints()
            self.check_win_conditions()
            return ActionResult(True, resolved)
        else:
            self.send_to_graveyard(player_idx, uid)
            self.state.log(f"{player.name} usa {card.definition.name} senza effetto implementato.")
        self._cleanup_zero_faith_saints()
        self.check_win_conditions()
        return ActionResult(True, "Carta giocata.")

    def activate_ability(self, player_idx: int, source: str, target: str | None = None) -> ActionResult:
        if player_idx != self.state.active_player:
            return ActionResult(False, "Puoi attivare abilita solo nel tuo turno.")
        uid = self.resolve_board_uid(player_idx, source)
        if uid is None:
            return ActionResult(False, "Sorgente non valida. Usa a1..a3, d1..d3, r1..r4 o b.")
        if "silenced" in self.state.instances[uid].cursed:
            return ActionResult(False, "Questa carta ha i suoi effetti annullati.")
        msg = resolve_activated_effect(self, player_idx, uid, target)
        self._cleanup_zero_faith_saints()
        self.check_win_conditions()
        return ActionResult(True, msg)

    def can_activate_once_per_turn(self, uid: str) -> bool:
        used = self.state.flags.setdefault("activated_turn", {})
        return int(used.get(uid, -1)) != int(self.state.turn_number)

    def mark_activated_this_turn(self, uid: str) -> None:
        used = self.state.flags.setdefault("activated_turn", {})
        used[uid] = int(self.state.turn_number)

    def quick_play(self, player_idx: int, hand_index: int, target: str | None = None) -> ActionResult:
        player = self.state.players[player_idx]
        card = self.card_from_hand(player_idx, hand_index)
        if card is None:
            return ActionResult(False, "Indice mano non valido.")
        ctype = _norm(card.definition.card_type)
        is_moribondo = _norm(card.definition.name) == _norm("Moribondo")
        if ctype not in QUICK_TYPES and not is_moribondo:
            return ActionResult(False, "Solo Benedizione/Maledizione (o Moribondo) sono giocabili fuori turno.")
        uid = player.hand.pop(hand_index)
        self._emit_event("on_card_played", player_idx, card=uid, card_type=ctype, target=target)
        if ctype == "benedizione":
            self._emit_event("on_blessing_played", player_idx, card=uid, target=target)
        elif ctype == "maledizione":
            self._emit_event("on_curse_played", player_idx, card=uid, target=target)
        if ctype in QUICK_TYPES and self._consume_counter_spell(player_idx):
            self.send_to_graveyard(player_idx, uid)
            self.state.log(f"{player.name} prova a usare {card.definition.name}, ma viene annullata da Barriera Magica.")
            return ActionResult(True, "Attivazione annullata da Barriera Magica.")
        if is_moribondo:
            target_card = self.resolve_target_saint(player_idx, target)
            if target_card is None:
                own = self.all_saints_on_field(player_idx)
                target_card = self.state.instances[own[0]] if own else None
            if target_card is None:
                player.hand.insert(hand_index, uid)
                return ActionResult(False, "Nessun santo valido da proteggere con Moribondo.")
            player.excommunicated.append(uid)
            target_card.blessed.append("moribondo_shield")
            self._cleanup_zero_faith_saints()
            self.check_win_conditions()
            return ActionResult(True, f"{player.name} scomunica Moribondo e protegge {target_card.definition.name}.")
        resolved = resolve_card_effect(self, player_idx, uid, target)
        self.send_to_graveyard(player_idx, uid)
        self._cleanup_zero_faith_saints()
        self.check_win_conditions()
        return ActionResult(True, resolved)

    def move_attack_positions(self, player_idx: int, from_slot: int, to_slot: int) -> ActionResult:
        if player_idx != self.state.active_player:
            return ActionResult(False, "Movimento disponibile solo nel tuo turno.")
        player = self.state.players[player_idx]
        if not (0 <= from_slot < ATTACK_SLOTS and 0 <= to_slot < ATTACK_SLOTS):
            return ActionResult(False, "Slot non valido.")
        player.attack[from_slot], player.attack[to_slot] = player.attack[to_slot], player.attack[from_slot]
        return ActionResult(True, "Santi in attacco scambiati.")

    def attack(self, player_idx: int, from_slot: int, target_slot: int | None) -> ActionResult:
        if self.state.phase == "preparation":
            return ActionResult(False, "Durante il turno di preparazione non si puo attaccare.")
        if int(self.state.flags.get("no_attacks_turn", -1)) == int(self.state.turn_number):
            return ActionResult(False, "In questo turno gli attacchi sono bloccati da un effetto.")
        if player_idx != self.state.active_player:
            return ActionResult(False, "Puoi attaccare solo nel tuo turno.")
        runtime_state = ensure_runtime_state(self)
        if not bool(runtime_state.get("battle_phase_started", False)):
            runtime_state["battle_phase_started"] = True
            set_phase(self, "battle")
            self._emit_event("on_battle_phase_start", player_idx, player=player_idx)
            refresh_player_flags(self)
        attacker_player = self.state.players[player_idx]
        defender_idx = 1 - player_idx
        defender_player = self.state.players[defender_idx]
        if not (0 <= from_slot < ATTACK_SLOTS):
            return ActionResult(False, "Slot attacco non valido.")
        attacker_uid = attacker_player.attack[from_slot]
        if attacker_uid is None:
            return ActionResult(False, "Nessun Santo in quello slot.")
        attacker = self.state.instances[attacker_uid]
        self._emit_event("on_attack_declared", player_idx, attacker=attacker_uid, target_slot=target_slot)
        self._emit_event("on_this_card_attacks", player_idx, card=attacker_uid, target_slot=target_slot)
        attacker_name_key = _norm(attacker.definition.name)
        if self._has_artifact(defender_idx, "Geroglifici"):
            cv = attacker.definition.crosses
            try:
                cv_int = int(float(cv)) if cv is not None else None
            except ValueError:
                cv_int = None
            if cv_int is not None and cv_int <= 2:
                return ActionResult(False, "Geroglifici impedisce l'attacco ai santi con croci <= 2.")
        if attacker_name_key == _norm("Giorno 5: Creature del Mare") and attacker_player.inspiration <= 2:
            return ActionResult(False, "Giorno 5 puo attaccare solo con Ispirazione rimanente > 2.")
        if attacker_name_key == _norm("Giorno 6: Creature di Terra") and attacker_player.inspiration >= 5:
            return ActionResult(False, "Giorno 6 puo attaccare solo con Ispirazione rimanente < 5.")
        if self._is_attacker_blocked_this_turn(attacker):
            return ActionResult(False, f"{attacker.definition.name} non puo attaccare in questo turno.")
        if attacker.exhausted:
            return ActionResult(False, "Questo Santo ha gia attaccato nel turno corrente.")
        attack_count = self.state.flags.setdefault("attack_count", {"0": 0, "1": 0})
        if (self._has_artifact(player_idx, "Sabbie Mobili") or self._has_artifact(defender_idx, "Sabbie Mobili")) and int(
            attack_count.get(str(player_idx), 0)
        ) >= 1:
            return ActionResult(False, "Con Sabbie Mobili attiva puoi attaccare con un solo Santo per turno.")

        if all(slot is None for slot in defender_player.attack + defender_player.defense):
            attacker.exhausted = True
            attack_count[str(player_idx)] = int(attack_count.get(str(player_idx), 0)) + 1
            if self._consume_attack_shield(defender_idx):
                self.state.log(f"{defender_player.name} annulla il primo attacco ricevuto in questo turno.")
                return ActionResult(True, "Attacco annullato da effetto di scudo.")
            if attacker_name_key == _norm("Fenrir"):
                attacker.definition.strength = (attacker.definition.strength or 0) + 1
            if attacker_name_key == _norm("Jormungandr"):
                attacker.current_faith = (attacker.current_faith or 0) + 1
            base_strength = max(0, attacker.definition.strength or 0)
            damage = self.get_effective_strength(attacker_uid)
            defender_player.sin += damage
            self._emit_event(
                "on_this_card_deals_damage",
                player_idx,
                card=attacker_uid,
                target_player=defender_idx,
                amount=damage,
            )
            self.state.log(
                f"{attacker_player.name} attacca con {attacker.definition.name} direttamente {defender_player.name} "
                f"(Forza base {base_strength}, effettiva {damage}) (+{damage} Peccato)."
            )
            self._apply_fiamma_primordiale_after_attack(player_idx, defender_idx, attacker_uid)
            self.check_win_conditions()
            return ActionResult(True, f"Attacco diretto riuscito: +{damage} Peccato all'avversario.")

        if target_slot is None or not (0 <= target_slot < ATTACK_SLOTS):
            return ActionResult(False, "Indica bersaglio valido t1..t3.")
        set_slot = next(
            (
                i
                for i, s_uid in enumerate(defender_player.attack)
                if s_uid and _norm(self.state.instances[s_uid].definition.name) == _norm("Set")
            ),
            None,
        )
        if set_slot is not None and target_slot != set_slot:
            return ActionResult(False, "Finche Set e in campo, deve essere l'unico bersaglio attaccabile.")
        defender_uid = defender_player.attack[target_slot]
        if defender_uid is None:
            return ActionResult(False, "Nessun Santo avversario nel bersaglio scelto.")
        defender_name = self.state.instances[defender_uid].definition.name
        if runtime_cards.get_attack_targeting_mode(defender_name) == "untargetable":
            return ActionResult(False, f"{defender_name} non puo essere bersagliato dagli attacchi.")
        if runtime_cards.get_attack_targeting_mode(defender_name) == "only_if_no_other_attackers":
            others = [u for i, u in enumerate(defender_player.attack) if i != target_slot and u is not None]
            if others:
                return ActionResult(False, f"{defender_name} puo essere bersagliato solo se non ci sono altri santi in attacco.")

        attacker.exhausted = True
        attack_count[str(player_idx)] = int(attack_count.get(str(player_idx), 0)) + 1
        if self._consume_attack_shield(defender_idx):
            self.state.log(f"{defender_player.name} annulla il primo attacco ricevuto in questo turno.")
            return ActionResult(True, "Attacco annullato da effetto di scudo.")
        if attacker_name_key == _norm("Fenrir"):
            attacker.definition.strength = (attacker.definition.strength or 0) + 1
        if attacker_name_key == _norm("Jormungandr"):
            attacker.current_faith = (attacker.current_faith or 0) + 1

        defender = self.state.instances[defender_uid]
        barrier = self._consume_barrier(defender)
        if barrier:
            self.state.log(f"{defender.definition.name} blocca l'attacco grazie a {barrier}.")
            self._apply_fiamma_primordiale_after_attack(player_idx, defender_idx, attacker_uid)
            return ActionResult(True, "Attacco annullato da barriera.")

        base_strength = max(0, attacker.definition.strength or 0)
        damage = self.get_effective_strength(attacker_uid)
        jordh_active = any(
            uid and _norm(self.state.instances[uid].definition.name) == _norm("Jordh")
            for uid in defender_player.attack + defender_player.defense
        )
        if jordh_active:
            before_damage = damage
            damage = max(0, damage // 2)
            self.state.log(f"Jordh modifica il danno: {before_damage}->{damage}.")
        damage = self._apply_damage_mitigation(defender_idx, damage)
        def_faith = defender.current_faith or 0
        if damage <= 0:
            self.state.log(
                f"{attacker_player.name} attacca con {attacker.definition.name} contro {defender.definition.name}, ma non infligge danni."
            )
            return ActionResult(True, "Nessun danno inflitto.")

        before_def = def_faith
        defender.current_faith = max(0, def_faith - damage)
        self._emit_event(
            "on_this_card_deals_damage",
            player_idx,
            card=attacker_uid,
            target=defender_uid,
            amount=damage,
        )
        self._emit_event(
            "on_this_card_receives_damage",
            defender_idx,
            card=defender_uid,
            source=attacker_uid,
            amount=damage,
        )
        after_def = defender.current_faith or 0
        self.state.log(
            f"{attacker_player.name} attacca con {attacker.definition.name} contro {defender.definition.name} "
            f"(Forza base {base_strength}, effettiva {damage}) e infligge {damage} danni (Fede {before_def}->{after_def})."
        )
        lethal = (defender.current_faith or 0) <= 0
        if lethal:
            excommunicate = runtime_cards.get_battle_excommunicate_on_lethal(attacker.definition.name)
            self.destroy_saint_by_uid(self.state.instances[defender_uid].owner, defender_uid, excommunicate=excommunicate, cause="battle")
            self._emit_event("on_this_card_kills_in_battle", player_idx, card=attacker_uid, victim=defender_uid)
            if attacker_name_key == _norm("Golem di Pietra"):
                attacker.current_faith = 4
            if attacker_name_key == _norm("Sequoia"):
                attacker.definition.strength = (attacker.definition.strength or 0) * 2
            if attacker_name_key == _norm("Odino"):
                attacker.definition.strength = (attacker.definition.strength or 0) + 2
        elif attacker_name_key == _norm("Odino"):
            attacker.definition.strength = (attacker.definition.strength or 0) + 1
        else:
            if _norm(defender.definition.name) == _norm("Schiavi") and damage > 0:
                defender.current_faith = (defender.current_faith or 0) + 2

        # Retaliation effects for Stalagmiti / Stalattiti (card-specific, not base combat).
        defender_name_key = _norm(defender.definition.name)
        if not lethal and defender_name_key in {_norm("Stalagmiti"), _norm("Stalattiti")}:
            retaliation = 3 if defender_name_key == _norm("Stalagmiti") else 2
            retaliation = self._apply_damage_mitigation(player_idx, retaliation)
            before = attacker.current_faith or 0
            attacker.current_faith = max(0, (attacker.current_faith or 0) - retaliation)
            after = attacker.current_faith or 0
            self.state.log(
                f"{attacker.definition.name} subisce {retaliation} danni di ritorsione (Fede {before}->{after})."
            )
            if (attacker.current_faith or 0) <= 0:
                self.destroy_saint_by_uid(self.state.instances[attacker_uid].owner, attacker_uid, cause="battle")

        forced_destroy: list[tuple[int, str]] = []
        attacker_on_board = attacker_uid in (attacker_player.attack + attacker_player.defense)
        defender_on_board = defender_uid in (defender_player.attack + defender_player.defense)
        if runtime_cards.get_post_battle_forced_destroy(attacker.definition.name) and attacker_on_board:
            forced_destroy.append((player_idx, attacker_uid))
            if defender_on_board:
                forced_destroy.append((defender_idx, defender_uid))
        if runtime_cards.get_post_battle_forced_destroy(defender.definition.name) and defender_on_board:
            forced_destroy.append((defender_idx, defender_uid))
            if attacker_on_board:
                forced_destroy.append((player_idx, attacker_uid))
        for owner_idx, forced_uid in forced_destroy:
            if forced_uid not in (self.state.players[owner_idx].attack + self.state.players[owner_idx].defense):
                continue
            faith_val = max(0, self.state.instances[forced_uid].definition.faith or 0)
            self.destroy_saint_by_uid(self.state.instances[forced_uid].owner, forced_uid, cause="effect")
            self.gain_sin(0, faith_val)
            self.gain_sin(1, faith_val)

        self._apply_fiamma_primordiale_after_attack(player_idx, defender_idx, attacker_uid)
        self.check_win_conditions()
        return ActionResult(True, f"Danno inflitto: {damage}.")

    def _kill_saint(self, owner_idx: int, attack_slot: int) -> None:
        player = self.state.players[owner_idx]
        uid = player.attack[attack_slot]
        if uid is None:
            return
        self.destroy_saint_by_uid(self.state.instances[uid].owner, uid, cause="battle")

    def send_to_graveyard(
        self,
        owner_idx: int,
        uid: str,
        token_to_white: bool = False,
        from_zone_override: str | None = None,
    ) -> None:
        card = self.state.instances[uid]
        board_owner_idx = self._find_board_owner_of_uid(uid)
        if board_owner_idx is None:
            board_owner_idx = owner_idx
        player = self.state.players[board_owner_idx]
        from_zone = from_zone_override or self._locate_uid_zone(board_owner_idx, uid)
        grave_target_idx = owner_idx

        for tag in list(card.blessed):
            if tag.startswith("grave_to_owner:"):
                try:
                    grave_target_idx = int(tag.split(":", 1)[1])
                except ValueError:
                    grave_target_idx = owner_idx
                card.blessed.remove(tag)

        leaving_field = from_zone in {"attack", "defense", "artifact", "building"}

        if _norm(card.definition.card_type) == "token" and token_to_white:
            if uid not in self.state.players[grave_target_idx].white_deck:
                self.state.players[grave_target_idx].white_deck.insert(0, uid)

        if uid not in self.state.players[grave_target_idx].graveyard:
            self.state.players[grave_target_idx].graveyard.append(uid)

        self._remove_from_board(player, uid)

        if leaving_field:
            self._reset_card_runtime_state(uid)

        self._emit_event(
            "on_card_sent_to_graveyard",
            owner_idx,
            card=uid,
            from_zone=from_zone,
            owner=grave_target_idx,
        )
        if leaving_field:
            self._emit_event("on_this_card_leaves_field", owner_idx, card=uid, destination="graveyard")

    def excommunicate_card(self, owner_idx: int, uid: str, from_zone_override: str | None = None) -> None:
        board_owner_idx = self._find_board_owner_of_uid(uid)
        if board_owner_idx is None:
            board_owner_idx = owner_idx
        player = self.state.players[board_owner_idx]
        from_zone = from_zone_override or self._locate_uid_zone(board_owner_idx, uid)

        leaving_field = from_zone in {"attack", "defense", "artifact", "building"}

        if uid not in player.excommunicated:
            player.excommunicated.append(uid)

        self._remove_from_board(player, uid)

        if leaving_field:
            self._reset_card_runtime_state(uid)

        self._emit_event(
            "on_card_excommunicated",
            owner_idx,
            card=uid,
            from_zone=from_zone,
            owner=owner_idx,
        )
        if leaving_field:
            self._emit_event("on_this_card_leaves_field", owner_idx, card=uid, destination="excommunicated")

    def absolve_card_to_graveyard(self, owner_idx: int, uid: str) -> None:
        player = self.state.players[owner_idx]
        if uid in player.excommunicated:
            player.excommunicated.remove(uid)
            player.graveyard.append(uid)

    def _remove_from_board(self, player: PlayerState, uid: str) -> None:
        for i, slot_uid in enumerate(player.attack):
            if slot_uid == uid:
                player.attack[i] = None
        for i, slot_uid in enumerate(player.defense):
            if slot_uid == uid:
                player.defense[i] = None
        for i, slot_uid in enumerate(player.artifacts):
            if slot_uid == uid:
                player.artifacts[i] = None
        if player.building == uid:
            player.building = None

    def _parse_zone_target(self, target: str | None) -> tuple[str | None, int]:
        if not target:
            return None, -1
        value = target.strip().lower()
        if len(value) != 2:
            return None, -1
        zone_char, slot_char = value[0], value[1]
        if not slot_char.isdigit():
            return None, -1
        slot = int(slot_char) - 1
        if slot < 0 or slot >= 3:
            return None, -1
        if zone_char == "a":
            return "attack", slot
        if zone_char == "d":
            return "defense", slot
        return None, -1

    def _first_open(self, slots: list[str | None]) -> int | None:
        for idx, val in enumerate(slots):
            if val is None:
                return idx
        return None

    def _consume_barrier(self, defender: CardInstance) -> str | None:
        for barrier_name in ("Barriera Magica",):
            if barrier_name in defender.blessed:
                defender.blessed.remove(barrier_name)
                return barrier_name
        return None

    def _apply_damage_mitigation(self, target_owner_idx: int, damage: int) -> int:
        if damage <= 0:
            return 0
        if self._has_artifact(target_owner_idx, "Rifugio Sacro") and damage < 3:
            return 0
        return damage

    def _is_attacker_blocked_this_turn(self, attacker: CardInstance) -> bool:
        keep: list[str] = []
        blocked = False
        for tag in attacker.cursed:
            if not tag.startswith("no_attack_until:"):
                keep.append(tag)
                continue
            try:
                until_turn = int(tag.split(":", 1)[1])
            except ValueError:
                continue
            if self.state.turn_number <= until_turn:
                blocked = True
                keep.append(tag)
        attacker.cursed = keep
        return blocked

    def _consume_attack_shield(self, defender_idx: int) -> bool:
        shield = self.state.flags.setdefault("attack_shield_turn", {})
        key = str(defender_idx)
        if int(shield.get(key, -1)) != int(self.state.turn_number):
            return False
        shield.pop(key, None)
        return True

    def _consume_counter_spell(self, caster_idx: int) -> bool:
        flags = self.state.flags.setdefault("counter_spell_ready", {"0": 0, "1": 0})
        opp_key = str(1 - caster_idx)
        count = int(flags.get(opp_key, 0))
        if count <= 0:
            return False
        flags[opp_key] = count - 1
        return True

    def resolve_target_saint(self, player_idx: int, target: str | None) -> CardInstance | None:
        if not target:
            return None
        value = target.strip().lower()
        if len(value) != 2:
            return None
        zone, slot = self._parse_zone_target(value)
        if zone not in {"attack", "defense"}:
            return None
        player = self.state.players[player_idx]
        uid = getattr(player, zone)[slot]
        if uid is None:
            return None
        inst = self.state.instances[uid]
        if "untargetable_effects" in inst.blessed:
            return None
        return inst

    def resolve_target_artifact_or_building(self, player_idx: int, target: str | None) -> str | None:
        if not target:
            return None
        value = target.strip().lower()
        player = self.state.players[player_idx]
        if value.startswith("r") and len(value) == 2 and value[1].isdigit():
            idx = int(value[1]) - 1
            if 0 <= idx < ARTIFACT_SLOTS:
                return player.artifacts[idx]
        if value == "b":
            return player.building
        return None

    def resolve_board_uid(self, player_idx: int, source: str | None) -> str | None:
        if not source:
            return None
        value = source.strip().lower()
        zone, slot = self._parse_zone_target(value)
        player = self.state.players[player_idx]
        if zone in {"attack", "defense"}:
            return getattr(player, zone)[slot]
        return self.resolve_target_artifact_or_building(player_idx, value)

    def remove_from_board_no_sin(self, owner_idx: int, uid: str) -> None:
        board_owner_idx = self._find_board_owner_of_uid(uid)
        if board_owner_idx is None:
            board_owner_idx = owner_idx
        player = self.state.players[board_owner_idx]
        if uid not in player.graveyard:
            player.graveyard.append(uid)
        self._remove_from_board(player, uid)

    def _apply_fiamma_primordiale_after_attack(self, attacker_idx: int, defender_idx: int, attacker_uid: str) -> None:
        if not self._has_building(defender_idx, "Fiamma Primordiale"):
            return
        if attacker_uid not in self.state.instances:
            return
        attacker_player = self.state.players[attacker_idx]
        if attacker_uid not in (attacker_player.attack + attacker_player.defense):
            return
        attacker = self.state.instances[attacker_uid]
        burn = 2 * (2 ** self._count_artifact(defender_idx, "Incendio"))
        burn = self._apply_damage_mitigation(attacker_idx, burn)
        if burn <= 0 or (attacker.current_faith or 0) <= 0:
            return
        before = attacker.current_faith or 0
        attacker.current_faith = max(0, (attacker.current_faith or 0) - burn)
        after = attacker.current_faith or 0
        self.state.log(
            f"{attacker.definition.name} subisce {burn} danni da Fiamma Primordiale (post-combattimento) (Fede {before}->{after})."
        )
        if (attacker.current_faith or 0) <= 0:
            self.destroy_saint_by_uid(self.state.instances[attacker_uid].owner, attacker_uid, cause="effect")
            self.reduce_sin(defender_idx, 2)

    def destroy_any_card(self, owner_idx: int, uid: str) -> None:
        if uid is None:
            return
        ctype = _norm(self.state.instances[uid].definition.card_type)
        if ctype in SAINT_TYPES:
            self.destroy_saint_by_uid(self.state.instances[uid].owner, uid, cause="effect")
        else:
            self.send_to_graveyard(owner_idx, uid)

    def _apply_cataclisma_ciclico(self, active_idx: int) -> None:
        if not self._has_artifact(active_idx, "Cataclisma Ciclico"):
            return
        own_saints = self.all_saints_on_field(active_idx)
        opp_idx = 1 - active_idx
        opp_saints = self.all_saints_on_field(opp_idx)
        if not own_saints and not opp_saints:
            return
        if opp_saints:
            target_uid = opp_saints[0]
            target_owner = opp_idx
        else:
            target_uid = own_saints[0]
            target_owner = active_idx
        target_name = self.state.instances[target_uid].definition.name
        self.destroy_saint_by_uid(self.state.instances[target_uid].owner, target_uid, cause="effect")
        if target_owner == active_idx:
            self.gain_sin(opp_idx, 2)
            self.state.log(f"Cataclisma Ciclico distrugge {target_name}: +2 Peccato a {self.state.players[opp_idx].name}.")
        else:
            self.reduce_sin(active_idx, 1)
            self.state.log(f"Cataclisma Ciclico distrugge {target_name}: {self.state.players[active_idx].name} perde 1 Peccato.")

    def find_card_uid_in_deck(self, player_idx: int, name: str) -> str | None:
        player = self.state.players[player_idx]
        key = _norm(name)
        for uid in player.deck:
            if _norm(self.state.instances[uid].definition.name) == key:
                return uid
        return None

    def find_card_uid_in_graveyard(self, player_idx: int, name: str) -> str | None:
        player = self.state.players[player_idx]
        key = _norm(name)
        for uid in player.graveyard:
            if _norm(self.state.instances[uid].definition.name) == key:
                return uid
        return None

    def move_deck_card_to_hand(self, player_idx: int, uid: str) -> bool:
        player = self.state.players[player_idx]
        if uid not in player.deck:
            return False
        if len(player.hand) >= MAX_HAND:
            return False
        player.deck.remove(uid)
        player.hand.append(uid)
        return True

    def move_graveyard_card_to_hand(self, player_idx: int, uid: str) -> bool:
        player = self.state.players[player_idx]
        if uid not in player.graveyard or len(player.hand) >= MAX_HAND:
            return False
        player.graveyard.remove(uid)
        player.hand.append(uid)
        return True

    def move_board_card_to_hand(self, owner_idx: int, uid: str) -> bool:
        player = self.state.players[owner_idx]
        if len(player.hand) >= MAX_HAND:
            return False

        was_on_field = False

        if uid in player.attack:
            idx = player.attack.index(uid)
            player.attack[idx] = None
            was_on_field = True
        if uid in player.defense:
            idx = player.defense.index(uid)
            player.defense[idx] = None
            was_on_field = True
        if uid in player.artifacts:
            idx = player.artifacts.index(uid)
            player.artifacts[idx] = None
            was_on_field = True
        if player.building == uid:
            player.building = None
            was_on_field = True

        if was_on_field:
            self._reset_card_runtime_state(uid)

        if uid not in player.hand:
            player.hand.append(uid)
        return True

    def move_graveyard_card_to_deck_bottom(self, player_idx: int, uid: str) -> bool:
        player = self.state.players[player_idx]
        if uid not in player.graveyard:
            return False
        player.graveyard.remove(uid)
        player.deck.insert(0, uid)
        return True

    def _reset_effect_usage_this_turn(self) -> None:
        self.state.flags["effect_usage_per_turn"] = {}

    def _reset_turn_once_markers_this_turn(self) -> None:
        marker_prefix = "once_per_turn:"
        for inst in self.state.instances.values():
            keep = [tag for tag in inst.blessed if not tag.startswith(marker_prefix)]
            if len(keep) != len(inst.blessed):
                inst.blessed = keep

    def place_card_from_uid(self, player_idx: int, uid: str, zone: str, slot: int) -> bool:
        player = self.state.players[player_idx]
        if zone == "attack":
            if not (0 <= slot < ATTACK_SLOTS) or player.attack[slot] is not None:
                return False
            player.attack[slot] = uid
            return True
        if zone == "defense":
            if not (0 <= slot < DEFENSE_SLOTS) or player.defense[slot] is not None:
                return False
            player.defense[slot] = uid
            return True
        return False

    def empty_slots(self, player_idx: int, zone: str) -> list[int]:
        player = self.state.players[player_idx]
        slots = player.attack if zone == "attack" else player.defense
        return [i for i, uid in enumerate(slots) if uid is None]

    def available_expansions(self) -> list[str]:
        names = set()
        for inst in self.state.instances.values():
            if inst.definition.expansion:
                names.add(inst.definition.expansion)
        return sorted(names)

    def check_win_conditions(self) -> None:
        for idx, player in enumerate(self.state.players):
            if player.sin >= 100:
                self.state.winner = 1 - idx
                self.state.log(f"{player.name} ha raggiunto 100 Peccato. Vince {self.state.players[self.state.winner].name}.")
                return
            if not player.deck and not player.hand and all(slot is None for slot in player.attack + player.defense):
                self.state.winner = 1 - idx
                self.state.log(f"{player.name} ha esaurito tutte le carte giocabili. Vince {self.state.players[self.state.winner].name}.")
                return

    def export_logs(self, path: str | Path) -> Path:
        out = Path(path)
        out.write_text("\n".join(self.state.logs), encoding="utf-8")
        return out
