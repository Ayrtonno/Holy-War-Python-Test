from __future__ import annotations

import random
import unicodedata
from dataclasses import dataclass

from holywar.core.engine import ActionResult, GameEngine


SAINT_TYPES = {"santo", "token"}
QUICK_TYPES = {"benedizione", "maledizione"}


def _norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", text)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


def _safe_int(value: object, default: int = 0) -> int:
    if value is None:
        return default

    if isinstance(value, bool):
        return int(value)

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value)

    if isinstance(value, str):
        try:
            return int(float(value))
        except ValueError:
            return default

    return default


@dataclass(frozen=True)
class _Candidate:
    score: int
    hand_index: int
    target: str | None
    reason: str


def _is_affordable(engine: GameEngine, player_idx: int, hand_index: int) -> bool:
    player = engine.state.players[player_idx]
    card = engine.card_from_hand(player_idx, hand_index)
    if card is None:
        return False

    if _norm(card.definition.card_type) in QUICK_TYPES:
        return True

    try:
        cost = int(engine._calculate_play_cost(player_idx, hand_index, card))
    except Exception:
        cost = _safe_int(card.definition.faith)

    available = int(player.inspiration) + int(getattr(player, "temporary_inspiration", 0))
    return cost <= available


def _empty_slots(slots: list[str | None]) -> list[int]:
    return [idx for idx, uid in enumerate(slots) if uid is None]


def _card_value(engine: GameEngine, uid: str) -> int:
    inst = engine.state.instances[uid]
    return (
        _safe_int(inst.current_faith, _safe_int(inst.definition.faith)) * 2
        + max(0, engine.get_effective_strength(uid))
    )


def _best_enemy_attack_target(engine: GameEngine, opponent_idx: int, damage: int) -> int | None:
    opponent = engine.state.players[opponent_idx]
    candidates: list[tuple[int, int]] = []

    for slot, uid in enumerate(opponent.attack):
        if uid is None:
            continue

        inst = engine.state.instances[uid]
        faith = _safe_int(inst.current_faith, _safe_int(inst.definition.faith))
        value = _card_value(engine, uid)

        score = value + (40 if damage >= faith else 0) - max(0, faith - damage)
        candidates.append((score, slot))

    if not candidates:
        return None

    candidates.sort(reverse=True)
    return candidates[0][1]


def _best_own_blessing_target(engine: GameEngine, player_idx: int) -> str | None:
    player = engine.state.players[player_idx]
    candidates: list[tuple[int, str]] = []

    for prefix, slots in (("a", player.attack), ("d", player.defense)):
        for slot, uid in enumerate(slots):
            if uid is None:
                continue
            candidates.append((_card_value(engine, uid), f"{prefix}{slot + 1}"))

    if not candidates:
        return None

    candidates.sort(reverse=True)
    return candidates[0][1]


def _best_curse_target(engine: GameEngine, opponent_idx: int) -> str | None:
    opponent = engine.state.players[opponent_idx]
    candidates: list[tuple[int, str]] = []

    for prefix, slots in (("a", opponent.attack), ("d", opponent.defense)):
        for slot, uid in enumerate(slots):
            if uid is None:
                continue
            candidates.append((_card_value(engine, uid), f"{prefix}{slot + 1}"))

    for slot, uid in enumerate(opponent.artifacts):
        if uid is not None:
            candidates.append(
                (18 + _safe_int(engine.state.instances[uid].definition.faith), f"r{slot + 1}")
            )

    if opponent.building is not None:
        candidates.append(
            (25 + _safe_int(engine.state.instances[opponent.building].definition.faith), "b")
        )

    if not candidates:
        return None

    candidates.sort(reverse=True)
    return candidates[0][1]


def _saint_play_target(engine: GameEngine, player_idx: int, uid: str) -> str | None:
    player = engine.state.players[player_idx]
    inst = engine.state.instances[uid]

    strength = max(0, _safe_int(inst.definition.strength))
    attack_slots = _empty_slots(player.attack)
    defense_slots = _empty_slots(player.defense)

    if strength > 0 and attack_slots:
        return f"a{attack_slots[0] + 1}"

    if defense_slots:
        return f"d{defense_slots[0] + 1}"

    if attack_slots:
        return f"a{attack_slots[0] + 1}"

    return None


def _play_score(engine: GameEngine, player_idx: int, hand_index: int, target: str | None) -> int:
    card = engine.card_from_hand(player_idx, hand_index)
    if card is None:
        return -9999

    player = engine.state.players[player_idx]
    opponent = engine.state.players[1 - player_idx]

    ctype = _norm(card.definition.card_type)
    text = _norm(card.definition.effect_text)
    name = _norm(card.definition.name)

    faith = _safe_int(card.definition.faith)
    strength = max(0, _safe_int(card.definition.strength))

    score = 0

    if ctype in SAINT_TYPES:
        score = 30 + strength * 8 + faith * 3

        if target and target.startswith("a"):
            score += 8

        if ctype == "token":
            score -= 8

        if not any(player.attack + player.defense):
            score += 20

    elif ctype == "edificio":
        score = 42 + faith * 2

        if player.building is not None:
            score -= 25

    elif ctype == "artefatto":
        score = 36 + faith * 2

        if "forza" in text or "+" in text:
            score += 8

        if any(player.attack + player.defense):
            score += 8

    elif ctype == "maledizione":
        score = 34

        if target is not None:
            score += 15

        if any(opponent.attack):
            score += 10

        if any(word in text for word in ("distrugg", "escomunic", "danno", "peccato")):
            score += 12

    elif ctype == "benedizione":
        score = 26

        if target is not None:
            score += 12

        if any(word in text for word in ("forza", "fede", "annulla", "pesca")):
            score += 8

    elif ctype == "innata":
        score = 50

    if ctype in SAINT_TYPES and len([u for u in player.attack + player.defense if u]) >= 4:
        score -= 12

    if name == "moribondo":
        score -= 10

    return score


def _find_best_play(engine: GameEngine, player_idx: int) -> _Candidate | None:
    player = engine.state.players[player_idx]
    candidates: list[_Candidate] = []

    for i, uid in enumerate(list(player.hand)):
        if uid not in engine.state.instances:
            continue

        if not _is_affordable(engine, player_idx, i):
            continue

        card = engine.state.instances[uid]
        ctype = _norm(card.definition.card_type)
        target: str | None = None

        if ctype in SAINT_TYPES:
            target = _saint_play_target(engine, player_idx, uid)
            if target is None:
                continue

        elif ctype == "edificio":
            if player.building is not None:
                continue

        elif ctype == "benedizione":
            target = _best_own_blessing_target(engine, player_idx)
            if target is None:
                continue

        elif ctype == "maledizione":
            target = _best_curse_target(engine, 1 - player_idx)
            if target is None:
                continue

        elif ctype not in {"artefatto", "innata"}:
            continue

        score = _play_score(engine, player_idx, i, target)
        candidates.append(_Candidate(score, i, target, "play"))

    if not candidates:
        return None

    candidates.sort(key=lambda c: (c.score, -c.hand_index), reverse=True)
    return candidates[0]


def _find_best_attack(engine: GameEngine, player_idx: int) -> tuple[int, int | None, int] | None:
    player = engine.state.players[player_idx]
    opponent_idx = 1 - player_idx
    opponent = engine.state.players[opponent_idx]

    candidates: list[tuple[int, int, int | None]] = []

    for slot, uid in enumerate(player.attack):
        if uid is None:
            continue

        inst = engine.state.instances[uid]
        if inst.exhausted:
            continue

        damage = max(0, engine.get_effective_strength(uid))

        if all(x is None for x in opponent.attack + opponent.defense):
            score = 100 + damage * 10
            candidates.append((score, slot, None))
            continue

        target = _best_enemy_attack_target(engine, opponent_idx, damage)
        if target is None:
            continue

        defender_uid = opponent.attack[target]
        if defender_uid is None:
            continue

        defender = engine.state.instances[defender_uid]
        defender_faith = _safe_int(defender.current_faith, _safe_int(defender.definition.faith))

        score = 45 + damage * 6 + _card_value(engine, defender_uid)

        if damage >= defender_faith:
            score += 35

        candidates.append((score, slot, target))

    if not candidates:
        return None

    candidates.sort(reverse=True)
    score, slot, target = candidates[0]
    return slot, target, score


def choose_action(engine: GameEngine, player_idx: int, rng: random.Random) -> ActionResult:
    if engine.state.winner is not None:
        return ActionResult(True, "AI passa.")

    if player_idx != engine.state.active_player:
        return ActionResult(True, "AI passa.")

    best_play = _find_best_play(engine, player_idx)
    best_attack = _find_best_attack(engine, player_idx)

    if best_attack is not None:
        attack_slot, target_slot, attack_score = best_attack
        play_score = best_play.score if best_play is not None else -9999

        if best_play is None or attack_score >= play_score + 20:
            res = engine.attack(player_idx, attack_slot, target_slot)
            if res.ok:
                return res

    if best_play is not None:
        res = engine.play_card(player_idx, best_play.hand_index, best_play.target)
        if res.ok:
            return res

    if best_attack is not None:
        attack_slot, target_slot, _score = best_attack
        res = engine.attack(player_idx, attack_slot, target_slot)
        if res.ok:
            return res

    player = engine.state.players[player_idx]
    opponent = engine.state.players[1 - player_idx]

    for slot, uid in enumerate(player.attack):
        if uid and not engine.state.instances[uid].exhausted:
            available_targets = [i for i in range(3) if opponent.attack[i] is not None]
            target = rng.choice(available_targets) if available_targets else None

            res = engine.attack(player_idx, slot, target)
            if res.ok:
                return res

    return ActionResult(True, "AI passa.")