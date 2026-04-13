from __future__ import annotations

import random
import unicodedata

from holywar.core.engine import ActionResult, GameEngine


def _norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", text)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


def choose_action(engine: GameEngine, player_idx: int, rng: random.Random) -> ActionResult:
    player = engine.state.players[player_idx]
    opponent = engine.state.players[1 - player_idx]

    # Try to play a saint/token first if possible and affordable.
    for i, uid in enumerate(list(player.hand)):
        card = engine.state.instances[uid]
        ctype = _norm(card.definition.card_type)
        cost = card.definition.faith or 0
        if cost > player.inspiration:
            continue
        if ctype in {"santo", "token"}:
            for slot in range(3):
                if player.attack[slot] is None:
                    res = engine.play_card(player_idx, i, f"a{slot + 1}")
                    if res.ok:
                        return res
                if player.defense[slot] is None:
                    res = engine.play_card(player_idx, i, f"d{slot + 1}")
                    if res.ok:
                        return res

    # Then try artifacts/buildings if affordable.
    for i, uid in enumerate(list(player.hand)):
        card = engine.state.instances[uid]
        ctype = _norm(card.definition.card_type)
        cost = card.definition.faith or 0
        if cost > player.inspiration:
            continue
        if ctype in {"artefatto", "edificio"}:
            res = engine.play_card(player_idx, i, None)
            if res.ok:
                return res

    # Then try quick cards with a reasonable target.
    for i, uid in enumerate(list(player.hand)):
        card = engine.state.instances[uid]
        ctype = _norm(card.definition.card_type)
        if ctype in {"benedizione", "maledizione"}:
            target = None
            if ctype == "benedizione":
                for slot in range(3):
                    if player.attack[slot] is not None:
                        target = f"a{slot + 1}"
                        break
            else:
                for slot in range(3):
                    if opponent.attack[slot] is not None:
                        target = f"a{slot + 1}"
                        break
                if target is None:
                    for slot in range(4):
                        if opponent.artifacts[slot] is not None:
                            target = f"r{slot + 1}"
                            break
                if target is None and opponent.building is not None:
                    target = "b"
            res = engine.play_card(player_idx, i, target)
            if res.ok:
                return res

    # Attack with first available saint.
    for slot in range(3):
        uid = player.attack[slot]
        if uid and not engine.state.instances[uid].exhausted:
            available_targets = [i for i in range(3) if opponent.attack[i] is not None]
            tgt = rng.choice(available_targets) if available_targets else None
            res = engine.attack(player_idx, slot, tgt)
            if res.ok:
                return res

    return ActionResult(True, "AI passa.")
