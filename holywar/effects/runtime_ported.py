from __future__ import annotations

import re
import unicodedata
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from holywar.core.engine import GameEngine


def _norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", text)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


def _cross_value(crosses: str | None) -> int | None:
    if crosses is None:
        return None
    txt = _norm(crosses)
    if txt in {"white", "croce bianca"}:
        return 11
    try:
        return int(float(txt))
    except ValueError:
        return None


def _first_open_slot(engine: "GameEngine", player_idx: int) -> tuple[str, int] | None:
    att = engine.empty_slots(player_idx, "attack")
    if att:
        return "attack", att[0]
    deff = engine.empty_slots(player_idx, "defense")
    if deff:
        return "defense", deff[0]
    return None


def _damage_saint(engine: "GameEngine", uid: str, dmg: int) -> bool:
    if dmg <= 0:
        return False
    inst = engine.state.instances[uid]
    inst.current_faith = max(0, (inst.current_faith or 0) - dmg)
    if (inst.current_faith or 0) <= 0:
        engine.destroy_saint_by_uid(inst.owner, uid)
        return True
    return False


def _has_named_saint_on_field(engine: "GameEngine", player_idx: int, name: str) -> bool:
    key = _norm(name)
    for uid in engine.all_saints_on_field(player_idx):
        if _norm(engine.state.instances[uid].definition.name) == key:
            return True
    return False


def _iter_all_field_cards(engine: "GameEngine"):
    for pidx, player in enumerate(engine.state.players):
        for uid in player.attack + player.defense + player.artifacts:
            if uid:
                yield pidx, uid
        if player.building:
            yield pidx, player.building


def _extract_first_int(text: str) -> int | None:
    m = re.search(r"(\d+)", text)
    if not m:
        return None
    return int(m.group(1))


def _split_targets(target: str | None) -> list[str]:
    if not target:
        return []
    return [p.strip().lower() for p in target.split(",") if p.strip()]


def _pick_target_saint(
    engine: "GameEngine", owner_idx: int, target: str | None, prefer_own: bool
):
    idx = owner_idx if prefer_own else 1 - owner_idx
    chosen = engine.resolve_target_saint(idx, target)
    if chosen:
        if "untargetable_effects" in chosen.blessed:
            return None
        return chosen
    saints = engine.all_saints_on_field(idx)
    if not saints:
        return None
    candidate = engine.state.instances[saints[0]]
    if "untargetable_effects" in candidate.blessed:
        return None
    return candidate


def _pick_target_saints(
    engine: "GameEngine", owner_idx: int, target: str | None, prefer_own: bool, count: int
):
    idx = owner_idx if prefer_own else 1 - owner_idx
    picked: list = []
    for tok in _split_targets(target):
        c = engine.resolve_target_saint(idx, tok)
        if c and all(c.uid != p.uid for p in picked):
            picked.append(c)
            if len(picked) >= count:
                return picked
    for s_uid in engine.all_saints_on_field(idx):
        c = engine.state.instances[s_uid]
        if all(c.uid != p.uid for p in picked):
            picked.append(c)
            if len(picked) >= count:
                break
    return picked


def _extract_quoted_names(text: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"\"([^\"]+)\"", text)]


def _find_in_list_by_name(engine: "GameEngine", uid_list: list[str], names: list[str]) -> str | None:
    if not uid_list:
        return None
    if names:
        keys = {_norm(n) for n in names if n and _norm(n)}
        # 1) Exact match first.
        for c_uid in uid_list:
            cname = _norm(engine.state.instances[c_uid].definition.name)
            if cname in keys:
                return c_uid
        # 2) Partial/fuzzy match (useful for generic targets like "Sigillo").
        for c_uid in uid_list:
            cname = _norm(engine.state.instances[c_uid].definition.name)
            if any(k in cname or cname in k for k in keys):
                return c_uid
    return uid_list[-1]


def _find_in_list_by_type(engine: "GameEngine", uid_list: list[str], type_names: set[str], max_count: int = 1) -> list[str]:
    out: list[str] = []
    for c_uid in uid_list:
        ctype = _norm(engine.state.instances[c_uid].definition.card_type)
        if ctype in type_names:
            out.append(c_uid)
            if len(out) >= max_count:
                break
    return out


def _summon_uid_to_first_slot(engine: "GameEngine", player_idx: int, uid: str) -> bool:
    slot = _first_open_slot(engine, player_idx)
    if not slot:
        return False
    zone, idx = slot
    return engine.place_card_from_uid(player_idx, uid, zone, idx)


def _resolve_generic_text_effect(engine: "GameEngine", player_idx: int, uid: str, target: str | None) -> str | None:
    state = engine.state
    player = state.players[player_idx]
    opponent_idx = 1 - player_idx
    opponent = state.players[opponent_idx]
    card = state.instances[uid]
    text = _norm(card.definition.effect_text or "")
    raw_text = card.definition.effect_text or ""
    if not text:
        return None

    acted = False
    logs: list[str] = []

    # Draw effects.
    draw_total = 0
    draw_total += sum(int(m.group(1)) for m in re.finditer(r"pesca\s+(\d+)\s+cart", text))
    if "pesca una carta" in text:
        draw_total += 1
    if draw_total > 0:
        drawn = engine.draw_cards(player_idx, draw_total)
        acted = True
        logs.append(f"{player.name} pesca {drawn} carte.")

    if "scarta una carta e pescane due" in text:
        if player.hand:
            disc = player.hand.pop(0)
            player.graveyard.append(disc)
            drawn = engine.draw_cards(player_idx, 2)
            acted = True
            logs.append(f"{player.name} scarta 1 carta e pesca {drawn}.")

    # Sin gain / reduction.
    sin_to_opp = 0
    m = re.search(r"avversario ottiene\s*\+?(\d+)\s+peccato", text)
    if m:
        sin_to_opp += int(m.group(1))
    m = re.search(r"infliggi\s+(\d+)\s+punti?\s+peccato", text)
    if m:
        sin_to_opp += int(m.group(1))
    if sin_to_opp > 0:
        engine.gain_sin(opponent_idx, sin_to_opp)
        acted = True
        logs.append(f"{opponent.name} guadagna {sin_to_opp} Peccato.")

    m = re.search(r"rimuovi\s+(\d+)\s+punti?\s+peccato", text)
    if m:
        amount = int(m.group(1))
        engine.reduce_sin(player_idx, amount)
        acted = True
        logs.append(f"{player.name} rimuove {amount} Peccato.")

    # Heal / buff on own saints.
    m = re.search(r"conferisci\s*\+?(\d+)\s+fede\s+a\s+un\s+tuo\s+santo", text)
    if m:
        amount = int(m.group(1))
        target_card = _pick_target_saint(engine, player_idx, target, prefer_own=True)
        if target_card:
            target_card.current_faith = (target_card.current_faith or 0) + amount
            acted = True
            logs.append(f"{target_card.definition.name} ottiene +{amount} Fede.")
    m = re.search(r"conferisci\s*\+?(\d+)\s+fede\s+a\s+due\s+santi", text)
    if m:
        amount = int(m.group(1))
        targets = _pick_target_saints(engine, player_idx, target, prefer_own=True, count=2)
        if targets:
            for t in targets:
                t.current_faith = (t.current_faith or 0) + amount
            acted = True
            logs.append(f"{len(targets)} santi ricevono +{amount} Fede.")

    m = re.search(r"conferisci\s*\+?(\d+)\s+forza\s+ad\s+un\s+santo", text)
    if m:
        amount = int(m.group(1))
        target_card = _pick_target_saint(engine, player_idx, target, prefer_own=True)
        if target_card:
            target_card.blessed.append(f"buff_str:{amount}")
            acted = True
            logs.append(f"{target_card.definition.name} ottiene +{amount} Forza.")

    if "riportare la sua fede al valore iniziale" in text or "ripristina tutta la fede di un santo" in text:
        target_card = _pick_target_saint(engine, player_idx, target, prefer_own=True)
        if target_card:
            target_card.current_faith = max(0, target_card.definition.faith or 0)
            acted = True
            logs.append(f"{target_card.definition.name} ripristina la Fede iniziale.")

    # Equip-like effects.
    if "equipaggia" in text and "santo" in text:
        target_card = _pick_target_saint(engine, player_idx, target, prefer_own=True)
        if target_card:
            m = re.search(r"aumenta la sua fede di\s+(\d+)", text)
            if m:
                target_card.current_faith = (target_card.current_faith or 0) + int(m.group(1))
            if _norm(card.definition.name) == _norm("Bende Consacrate"):
                target_card.blessed.append("bende_consacrate")
            if _norm(card.definition.name) == _norm("Oggetti di Famiglia"):
                maxf = max(1, (target_card.definition.faith or 1) // 2)
                target_card.definition.faith = maxf
                target_card.current_faith = min(target_card.current_faith or maxf, maxf)
            if _norm(card.definition.name) == _norm("Mela del Peccato"):
                target_card.current_faith = (target_card.current_faith or 0) + 15
            acted = True
            logs.append(f"{card.definition.name} viene equipaggiata a {target_card.definition.name}.")

    # Damage / destroy effects.
    m = re.search(r"tutti i santi avversari perdono\s+(\d+)\s+fede", text)
    if m:
        amount = int(m.group(1))
        for s_uid in list(engine.all_saints_on_field(opponent_idx)):
            _damage_saint(engine, s_uid, amount)
        acted = True
        logs.append(f"Tutti i santi avversari perdono {amount} Fede.")

    m = re.search(r"tutti i santi sul (?:terreno|campo) perdono\s+(\d+)\s+fede", text)
    if m:
        amount = int(m.group(1))
        for idx in (0, 1):
            for s_uid in list(engine.all_saints_on_field(idx)):
                _damage_saint(engine, s_uid, amount)
        acted = True
        logs.append(f"Tutti i santi sul campo/terreno perdono {amount} Fede.")
    m = re.search(r"ogni santo sul (?:terreno|campo) perde\s+(\d+)", text)
    if m:
        amount = int(m.group(1))
        for idx in (0, 1):
            for s_uid in list(engine.all_saints_on_field(idx)):
                _damage_saint(engine, s_uid, amount)
        acted = True
        logs.append(f"Ogni santo sul campo/terreno perde {amount} Fede.")

    if "distruggi tutti i santi sul terreno" in text or text.startswith("distruggi tutti i santi"):
        for idx in (0, 1):
            for s_uid in list(engine.all_saints_on_field(idx)):
                engine.destroy_saint_by_uid(idx, s_uid, cause="effect")
        acted = True
        logs.append("Tutti i santi sul terreno vengono distrutti.")
    elif "distruggi un santo" in text or "distruggilo" in text:
        target_card = _pick_target_saint(engine, player_idx, target, prefer_own=False)
        if target_card:
            engine.destroy_saint_by_uid(opponent_idx, target_card.uid, cause="effect")
            acted = True
            logs.append(f"{target_card.definition.name} viene distrutto.")
    elif "distruggi invece due santi" in text:
        targets = _pick_target_saints(engine, player_idx, target, prefer_own=False, count=2)
        if targets:
            for t in targets:
                engine.destroy_saint_by_uid(opponent_idx, t.uid, cause="effect")
            acted = True
            logs.append(f"{len(targets)} santi avversari vengono distrutti.")

    # Attack limitation / shield.
    if (
        "non potra attaccare durante il prossimo turno" in text
        or "non puo attaccare nel suo prossimo turno" in text
    ):
        target_card = _pick_target_saint(engine, player_idx, target, prefer_own=False)
        if target_card:
            until_turn = state.turn_number + 1
            target_card.cursed.append(f"no_attack_until:{until_turn}")
            acted = True
            logs.append(f"{target_card.definition.name} non puo attaccare nel prossimo turno.")

    if "annulla il primo attacco che ricevi in questo turno" in text:
        shield = state.flags.setdefault("attack_shield_turn", {})
        shield[str(player_idx)] = int(state.turn_number)
        acted = True
        logs.append("Il primo attacco ricevuto in questo turno viene annullato.")

    if "nessun santo puo attaccare il turno in cui questa carta e stata attivata" in text:
        state.flags["no_attacks_turn"] = int(state.turn_number)
        acted = True
        logs.append("Nessun santo puo attaccare in questo turno.")

    # Search / recover cards (deck, graveyard, excommunicated).
    if "cerc" in text and "reliquiario" in text and ("aggiung" in text and "mano" in text):
        quoted = _extract_quoted_names(raw_text)
        desired_target = (target or "").strip()
        if ":" in desired_target:
            desired_target = desired_target.split(":", 1)[1].strip()
        if desired_target and not any(ch.isdigit() for ch in desired_target):
            quoted = [desired_target] + quoted
        picked_uid = _find_in_list_by_name(engine, player.deck, quoted)
        if picked_uid is None:
            # Type-based searches.
            max_count = 2 if "2 carte" in text else 1
            if "benedizione o maledizione" in text or "benedizione o una maledizione" in text:
                cands = _find_in_list_by_type(engine, player.deck, {"benedizione", "maledizione"}, max_count=max_count)
            elif "artefatto" in text:
                cands = _find_in_list_by_type(engine, player.deck, {"artefatto"}, max_count=max_count)
            elif "\"giorno\"" in _norm(raw_text) or " carte \"giorno\"" in _norm(raw_text):
                cands = [c_uid for c_uid in player.deck if "giorno" in _norm(state.instances[c_uid].definition.name)][:max_count]
            else:
                cands = []
            if cands:
                moved = 0
                for c_uid in cands:
                    if engine.move_deck_card_to_hand(player_idx, c_uid):
                        moved += 1
                if moved > 0:
                    if "mischia" in text:
                        engine.rng.shuffle(player.deck)
                    acted = True
                    logs.append(f"{player.name} cerca nel reliquiario e aggiunge {moved} carte alla mano.")
        if picked_uid is not None and engine.move_deck_card_to_hand(player_idx, picked_uid):
            if "mischia" in text:
                engine.rng.shuffle(player.deck)
            acted = True
            logs.append(f"{player.name} cerca nel reliquiario e aggiunge {state.instances[picked_uid].definition.name}.")

    if "cimitero" in text and ("aggiung" in text and "mano" in text):
        quoted = _extract_quoted_names(raw_text)
        desired_target = (target or "").strip()
        if ":" in desired_target:
            desired_target = desired_target.split(":", 1)[1].strip()
        if desired_target and not any(ch.isdigit() for ch in desired_target):
            quoted = [desired_target] + quoted
        picked_uid = _find_in_list_by_name(engine, player.graveyard, quoted)
        if picked_uid is not None and engine.move_graveyard_card_to_hand(player_idx, picked_uid):
            acted = True
            logs.append(f"{player.name} riprende {state.instances[picked_uid].definition.name} dal cimitero.")

    if "riporta tutte le carte dai cimiteri ai rispettivi reliquiari" in text:
        for idx in (0, 1):
            p = state.players[idx]
            while p.graveyard:
                c_uid = p.graveyard.pop()
                p.deck.insert(0, c_uid)
            engine.rng.shuffle(p.deck)
        acted = True
        logs.append("Tutte le carte dei cimiteri tornano ai reliquiari e vengono mischiate.")

    if "carta scomunicata" in text and "reliquiario" in text:
        quoted = _extract_quoted_names(raw_text)
        picked_uid = _find_in_list_by_name(engine, player.excommunicated, quoted)
        if picked_uid is not None:
            if picked_uid in player.excommunicated:
                player.excommunicated.remove(picked_uid)
            player.deck.insert(0, picked_uid)
            if "mischia" in text:
                engine.rng.shuffle(player.deck)
            acted = True
            logs.append(f"{player.name} rimette {state.instances[picked_uid].definition.name} scomunicata nel reliquiario.")

    if "scambia i santi in attacco dell'avversario con quelli in difesa" in text:
        opp = state.players[opponent_idx]
        opp.attack, opp.defense = opp.defense, opp.attack
        acted = True
        logs.append("Attacco e difesa avversari vengono scambiati.")

    if "scambialo con un santo in attacco" in text and "difesa sul tuo terreno" in text:
        toks = _split_targets(target)
        d_slot = None
        a_slot = None
        for tk in toks:
            if tk.startswith("d") and len(tk) == 2 and tk[1].isdigit():
                d_slot = int(tk[1]) - 1
            if tk.startswith("a") and len(tk) == 2 and tk[1].isdigit():
                a_slot = int(tk[1]) - 1
        if d_slot is None:
            d_slot = next((i for i, v in enumerate(player.defense) if v is not None), None)
        if a_slot is None:
            a_slot = next((i for i, v in enumerate(player.attack) if v is not None), None)
        if d_slot is not None and a_slot is not None and 0 <= d_slot < 3 and 0 <= a_slot < 3:
            player.attack[a_slot], player.defense[d_slot] = player.defense[d_slot], player.attack[a_slot]
            acted = True
            logs.append("Un tuo santo in difesa viene scambiato con uno in attacco.")

    if "evoca" in text and ("dal tuo cimitero" in text or "dal reliquiario" in text):
        quoted = _extract_quoted_names(raw_text)
        pool: list[tuple[str, str]] = []
        if "dal tuo cimitero" in text:
            for c_uid in player.graveyard:
                pool.append(("graveyard", c_uid))
        if "dal reliquiario" in text:
            for c_uid in player.deck:
                pool.append(("deck", c_uid))
        chosen: tuple[str, str] | None = None
        if quoted:
            keys = {_norm(q) for q in quoted}
            for src, c_uid in pool:
                if _norm(state.instances[c_uid].definition.name) in keys:
                    chosen = (src, c_uid)
                    break
        if chosen is None:
            for src, c_uid in pool:
                if _norm(state.instances[c_uid].definition.card_type) in {"santo", "token"}:
                    chosen = (src, c_uid)
                    break
        if chosen is not None:
            src, c_uid = chosen
            if src == "graveyard":
                player.graveyard.remove(c_uid)
            else:
                player.deck.remove(c_uid)
            if _summon_uid_to_first_slot(engine, player_idx, c_uid):
                acted = True
                logs.append(f"{player.name} evoca {state.instances[c_uid].definition.name}.")
            else:
                if src == "graveyard":
                    player.graveyard.append(c_uid)
                else:
                    player.deck.insert(0, c_uid)

    # Deck ordering / look effects: currently informational.
    if (
        "guarda le prime" in text
        or "guarda la prima carta del mazzo" in text
        or "guarda la carta in fondo al tuo reliquiario" in text
    ):
        acted = True
        logs.append("Effetto di visione reliquiario applicato (MVP: informativo).")

    if not acted:
        return None
    details = " ".join(logs)
    state.log(f"{player.name} usa {card.definition.name}: {details}")
    return f"{card.definition.name} risolta."


def resolve_enter_effect(engine: "GameEngine", player_idx: int, uid: str) -> str | None:
    state = engine.state
    player = state.players[player_idx]
    card = state.instances[uid]
    name_key = _norm(card.definition.name)

    if name_key == _norm("Huginn"):
        top = player.deck[-3:]
        if not top:
            return f"{player.name} attiva Huginn: reliquiario vuoto."
        odino_on_field = _has_named_saint_on_field(engine, player_idx, "Odino")
        chosen = None
        for c_uid in reversed(top):
            c = state.instances[c_uid]
            if odino_on_field:
                chosen = c_uid
                break
            if _norm(c.definition.card_type) == "santo":
                chosen = c_uid
                break
        if chosen and engine.move_deck_card_to_hand(player_idx, chosen):
            return f"{player.name} attiva Huginn e aggiunge {state.instances[chosen].definition.name} alla mano."
        return f"{player.name} attiva Huginn ma non trova un Santo valido tra le prime 3 carte."

    if name_key == _norm("Muninn"):
        if not player.graveyard:
            return None
        odino_on_field = _has_named_saint_on_field(engine, player_idx, "Odino")
        chosen = player.graveyard[-1]
        c_name = state.instances[chosen].definition.name
        if odino_on_field and engine.move_graveyard_card_to_hand(player_idx, chosen):
            return f"{player.name} attiva Muninn e riprende {c_name} in mano."
        if engine.move_graveyard_card_to_deck_bottom(player_idx, chosen):
            return f"{player.name} attiva Muninn e rimette {c_name} nel reliquiario."
        return None

    if name_key == _norm("Skadi"):
        opp = state.players[1 - player_idx]
        for opp_uid in opp.attack + opp.defense:
            if not opp_uid:
                continue
            inst = state.instances[opp_uid]
            if engine.get_effective_strength(opp_uid) >= 5:
                inst.definition.strength = max(0, (inst.definition.strength or 0) - 3)
                return f"{player.name} attiva Skadi: {inst.definition.name} perde 3 Forza."
        return None

    if name_key == _norm("Totem di Pietra"):
        spent = player.inspiration
        player.inspiration = 0
        card.current_faith = spent * 3
        return f"{player.name} attiva Totem di Pietra: Fede impostata a {card.current_faith}."

    if name_key == _norm("Sacerdote Orologio"):
        target_uid = None
        for s_uid in engine.all_saints_on_field(1 - player_idx):
            inst = state.instances[s_uid]
            cv = _cross_value(inst.definition.crosses)
            if cv is None or cv > 5:
                continue
            if (inst.current_faith or 0) >= (inst.definition.faith or 0):
                continue
            target_uid = s_uid
            break
        if target_uid:
            card.blessed = [t for t in card.blessed if not t.startswith("orologio_link:")]
            card.blessed.append(f"orologio_link:{target_uid}")
            return f"{player.name} collega Sacerdote Orologio a {state.instances[target_uid].definition.name}."
        return f"{player.name} attiva Sacerdote Orologio: nessun santo avversario danneggiato valido (Croci <= 5)."

    if name_key == _norm("Custode dei Sigilli"):
        b_uid = player.building
        if b_uid and _norm(state.instances[b_uid].definition.name) == _norm("Altare dei Sette Sigilli"):
            altar = state.instances[b_uid]
            sig = 0
            for tag in list(altar.blessed):
                if tag.startswith("sigilli:"):
                    try:
                        sig = int(tag.split(":", 1)[1])
                    except ValueError:
                        sig = 0
                    altar.blessed.remove(tag)
            sig += 2
            altar.blessed.append(f"sigilli:{sig}")
            bonus = (sig // 6) * 3
            if bonus > 0:
                card.blessed.append(f"buff_str:{bonus}")
                card.current_faith = (card.current_faith or 0) + bonus
            return f"{player.name} attiva Custode dei Sigilli: Altare +2 Sigilli."

    # Generic enter fallback for text-driven triggers.
    text = _norm(card.definition.effect_text or "")
    raw_text = card.definition.effect_text or ""
    acted = False
    logs: list[str] = []

    if "quando entra in campo" in text:
        m = re.search(r"infligge\s+(\d+)\s+dann[oi]\s+a\s+ogni\s+santo\s+avversario", text)
        if m:
            amount = int(m.group(1))
            for s_uid in list(engine.all_saints_on_field(1 - player_idx)):
                _damage_saint(engine, s_uid, amount)
            acted = True
            logs.append(f"Infligge {amount} danni a tutti i santi avversari.")

        m = re.search(r"ottiene\s*\+?(\d+)\s+fede\s+per\s+ogni\s+santo", text)
        if m and "avversario" in text:
            amount = int(m.group(1))
            count = len(engine.all_saints_on_field(1 - player_idx))
            gained = amount * count
            card.current_faith = (card.current_faith or 0) + gained
            acted = True
            logs.append(f"{card.definition.name} ottiene +{gained} Fede all'ingresso.")

        m = re.search(r"conferisce\s*\+?(\d+)\s+fede\s+a\s+ogni\s+santo\s+danneggiato", text)
        if m:
            amount = int(m.group(1))
            buffed = 0
            for s_uid in engine.all_saints_on_field(player_idx):
                inst = state.instances[s_uid]
                if (inst.current_faith or 0) < (inst.definition.faith or 0):
                    inst.current_faith = (inst.current_faith or 0) + amount
                    buffed += 1
            acted = True
            logs.append(f"{buffed} santi danneggiati ottengono +{amount} Fede.")

        if "cerc" in text and "reliquiario" in text and "aggiung" in text and "mano" in text:
            quoted = _extract_quoted_names(raw_text)
            picked = _find_in_list_by_name(engine, player.deck, quoted)
            if picked is None:
                if "santo" in text:
                    by_type = _find_in_list_by_type(engine, player.deck, {"santo", "token"}, max_count=1)
                    picked = by_type[0] if by_type else None
            if picked and engine.move_deck_card_to_hand(player_idx, picked):
                if "mischia" in text:
                    engine.rng.shuffle(player.deck)
                acted = True
                logs.append(f"{player.name} aggiunge {state.instances[picked].definition.name} alla mano.")

    if "non puo essere targettato da effetti" in text:
        if "untargetable_effects" not in card.blessed:
            card.blessed.append("untargetable_effects")
        acted = True
        logs.append(f"{card.definition.name} non puo essere bersagliato da effetti.")

    if "e immune alle maledizioni" in text:
        if "curse_immune" not in card.blessed:
            card.blessed.append("curse_immune")
        acted = True
        logs.append(f"{card.definition.name} e immune alle maledizioni.")

    if acted:
        return f"{player.name} attiva {card.definition.name}: {' '.join(logs)}"
    return None


def resolve_card_effect(engine: "GameEngine", player_idx: int, uid: str, target: str | None) -> str:
    state = engine.state
    player = state.players[player_idx]
    opponent_idx = 1 - player_idx
    opponent = state.players[opponent_idx]
    card = state.instances[uid]
    name_key = _norm(card.definition.name)
    ctype_key = _norm(card.definition.card_type)
    if ctype_key == "maledizione" and engine._has_artifact(opponent_idx, "Acqua"):
        return "Acqua protegge i santi avversari dalle maledizioni."
    if ctype_key == "maledizione" and target:
        t_opp = engine.resolve_target_saint(opponent_idx, target)
        if t_opp and "curse_immune" in t_opp.blessed:
            return f"{t_opp.definition.name} e immune alle maledizioni."

    # Neutre / baseline
    if name_key == _norm("Cura"):
        target_card = engine.resolve_target_saint(player_idx, target)
        if not target_card:
            return "Nessun bersaglio valido per Cura."
        amount = 3
        target_card.current_faith = (target_card.current_faith or 0) + amount
        state.log(f"{player.name} usa Cura su {target_card.definition.name}: +{amount} Fede.")
        return "Cura risolta."

    if name_key == _norm("Cura Rapida"):
        if not target:
            return "Cura Rapida: devi selezionare esattamente 2 tuoi Santi."
        tokens = [t.strip() for t in target.split(",") if t.strip()]
        if len(tokens) != 2:
            return "Cura Rapida: devi selezionare esattamente 2 tuoi Santi."
        picked: list = []
        seen: set[str] = set()
        for tk in tokens:
            saint = engine.resolve_target_saint(player_idx, tk)
            if saint is None:
                return "Cura Rapida: bersaglio non valido."
            if saint.uid in seen:
                return "Cura Rapida: devi selezionare due bersagli diversi."
            seen.add(saint.uid)
            picked.append(saint)
        amount = 3
        for saint in picked:
            saint.current_faith = (saint.current_faith or 0) + amount
        names = ", ".join(s.definition.name for s in picked)
        state.log(f"{player.name} usa Cura Rapida su {names}: +{amount} Fede a ciascuno.")
        return "Cura Rapida risolta."


    if name_key == _norm("Concentrazione"):
        drawn = engine.draw_cards(player_idx, 2)
        state.log(f"{player.name} usa Concentrazione e pesca {drawn} carta.")
        return "Concentrazione risolta."

    if name_key == _norm("Corruzione"):
        engine.gain_sin(opponent_idx, 3)
        state.log(f"{player.name} usa Corruzione: {opponent.name} +3 Peccato.")
        return "Corruzione risolta: +3 Peccato avversario."

    if name_key == _norm("Furia di Llakhnal"):
        if state.players[0].sin >= 50 or state.players[1].sin >= 50:
            return "Furia di Llakhnal non valida: entrambi i giocatori devono avere meno di 50 Peccato."
        engine.gain_sin(0, 15)
        engine.gain_sin(1, 15)
        return "Furia di Llakhnal risolta: entrambi i giocatori +15 Peccato."

    if name_key in {_norm("Proibizione Cristiana"), _norm("Proibizione Egizia"), _norm("Proibizione di Ph")}:
        target_card = engine.resolve_target_saint(opponent_idx, target)
        if not target_card:
            return "Bersaglio non valido per Proibizione."
        target_card.cursed.append("silenced")
        return f"{card.definition.name} risolta: effetto di {target_card.definition.name} annullato."

    if name_key == _norm("Genesi: Compimento"):
        has_custode = any(
            _norm(state.instances[s_uid].definition.name) == _norm("Custode della Creazione")
            for s_uid in engine.all_saints_on_field(player_idx)
        )
        if not has_custode:
            return "Genesi: Compimento non valida: Custode della Creazione non presente."
        state.winner = player_idx
        state.log(f"{player.name} risolve Genesi: Compimento e vince il duello.")
        return "Genesi: Compimento risolta: vittoria immediata."

    if name_key == _norm("Primo Sigillo"):
        b_uid = player.building
        if b_uid and _norm(state.instances[b_uid].definition.name) == _norm("Altare dei Sette Sigilli"):
            altar = state.instances[b_uid]
            sig = 0
            for tag in list(altar.blessed):
                if tag.startswith("sigilli:"):
                    try:
                        sig = int(tag.split(":", 1)[1])
                    except ValueError:
                        sig = 0
                    altar.blessed.remove(tag)
            sig += 2
            altar.blessed.append(f"sigilli:{sig}")
            return "Primo Sigillo risolta: Altare +2 Sigilli."
        found = engine.find_card_uid_in_deck(player_idx, "Altare dei Sette Sigilli")
        if found and engine.move_deck_card_to_hand(player_idx, found):
            engine.rng.shuffle(player.deck)
            return "Primo Sigillo risolta: Altare aggiunto alla mano."
        return "Primo Sigillo risolta."

    if name_key == _norm("Giorno 1: Cieli e Terra"):
        art_uid = next(
            (h_uid for h_uid in list(player.hand) if _norm(state.instances[h_uid].definition.card_type) == "artefatto"),
            None,
        )
        if art_uid is None:
            return "Nessun Artefatto in mano per Giorno 1."
        art = state.instances[art_uid]
        cost = max(0, (art.definition.faith or 0) // 2)
        if player.inspiration < cost:
            return "Ispirazione insufficiente per l'Artefatto di Giorno 1."
        player.inspiration -= cost
        player.hand.remove(art_uid)
        slot = next((i for i, v in enumerate(player.artifacts) if v is None), None)
        if slot is None:
            player.graveyard.append(art_uid)
            return "Nessuno slot Artefatto libero per Giorno 1."
        player.artifacts[slot] = art_uid
        return f"Giorno 1 risolta: posizionato {art.definition.name} a costo dimezzato."

    if name_key == _norm("Arca della salvezza"):
        keep_uids: set[str] = set()
        for tk in _split_targets(target):
            for idx in (0, 1):
                c = engine.resolve_target_saint(idx, tk)
                if c:
                    keep_uids.add(c.uid)
            if len(keep_uids) >= 2:
                break
        if len(keep_uids) < 2:
            # fallback: keep first 2 saints found
            for idx in (0, 1):
                for s_uid in engine.all_saints_on_field(idx):
                    keep_uids.add(s_uid)
                    if len(keep_uids) >= 2:
                        break
                if len(keep_uids) >= 2:
                    break
        for idx in (0, 1):
            for s_uid in list(engine.all_saints_on_field(idx)):
                if s_uid in keep_uids:
                    continue
                engine.destroy_saint_by_uid(idx, s_uid, cause="effect")
        return "Arca della salvezza risolta."

    if name_key == _norm("Passaggio all'Aldilà"):
        target_card = engine.resolve_target_saint(player_idx, target)
        if target_card is None:
            own = engine.all_saints_on_field(player_idx)
            target_card = state.instances[own[0]] if own else None
        if target_card is None:
            return "Nessun santo da sacrificare per Passaggio all'Aldilà."
        gain = max(0, engine.get_effective_strength(target_card.uid))
        engine.destroy_saint_by_uid(player_idx, target_card.uid, cause="effect")
        player.inspiration += gain
        return f"Passaggio all'Aldilà risolta: +{gain} Ispirazione."

    if name_key == _norm("Rinforzi"):
        a_idx = next((i for i, v in enumerate(player.attack) if v is not None), None)
        d_idx = next((i for i, v in enumerate(player.defense) if v is not None), None)
        if a_idx is None or d_idx is None:
            return "Rinforzi non valida: servono un santo in attacco e uno in difesa."
        player.attack[a_idx], player.defense[d_idx] = player.defense[d_idx], player.attack[a_idx]
        return "Rinforzi risolta: santi scambiati."

    if name_key == _norm("Ritorno Catastrofico"):
        target_card = engine.resolve_target_saint(player_idx, target)
        if target_card is None:
            return "Bersaglio non valido per Ritorno Catastrofico."
        owner = state.players[target_card.owner]
        engine._remove_from_board(owner, target_card.uid)
        owner.hand.append(target_card.uid)
        return "Ritorno Catastrofico risolta."

    if name_key == _norm("Elemosina"):
        target_card = engine.resolve_target_saint(player_idx, target)
        if target_card is None:
            own = engine.all_saints_on_field(player_idx)
            target_card = state.instances[own[0]] if own else None
        if target_card is None:
            return "Elemosina non valida: nessun tuo santo da spostare."
        dest_idx = opponent_idx
        slot = _first_open_slot(engine, dest_idx)
        if slot is None:
            return "Elemosina non valida: nessuno slot libero sul campo avversario."
        # Move card to opponent field for temporary control; on death it goes to original owner's graveyard.
        target_card.blessed.append(f"grave_to_owner:{target_card.owner}")
        engine._remove_from_board(player, target_card.uid)
        zone, sidx = slot
        engine.place_card_from_uid(dest_idx, target_card.uid, zone, sidx)
        return f"Elemosina risolta: {target_card.definition.name} passa temporaneamente al campo avversario."

    if name_key == _norm("Contemplazione"):
        spent = int(state.flags.setdefault("spent_inspiration_turn", {"0": 0, "1": 0}).get(str(player_idx), 0))
        if spent <= 7:
            return "Contemplazione: condizione non soddisfatta (servono oltre 7 Ispirazione spese nel turno)."
        bonus = state.flags.setdefault("bonus_inspiration_next_turn", {"0": 0, "1": 0})
        bonus[str(player_idx)] = int(bonus.get(str(player_idx), 0)) + 1
        return "Contemplazione risolta: +1 Ispirazione al prossimo turno."

    if name_key == _norm("Barriera Magica"):
        flags = state.flags.setdefault("counter_spell_ready", {"0": 0, "1": 0})
        flags[str(player_idx)] = int(flags.get(str(player_idx), 0)) + 1
        return "Barriera Magica attiva: annullera la prossima Benedizione/Maledizione avversaria."

    if name_key == _norm("Pietra Nera"):
        target_card = engine.resolve_target_saint(opponent_idx, target)
        if not target_card:
            return "Nessun bersaglio valido per Pietra Nera."
        target_card.blessed.append("Barriera Magica")
        state.log(f"{player.name} applica Pietra Nera a {target_card.definition.name}.")
        return "Pietra Nera applicata."

    if name_key == _norm("Barriera Magica Celestiale"):
        if player.hand:
            scarto = player.hand.pop(0)
            player.graveyard.append(scarto)
        flags = state.flags.setdefault("counter_spell_ready", {"0": 0, "1": 0})
        flags[str(player_idx)] = int(flags.get(str(player_idx), 0)) + 1
        return "Barriera Magica Celestiale attiva: prossima Benedizione/Maledizione avversaria annullata."

    if name_key == _norm("Ascensione"):
        target_card = engine.resolve_target_saint(player_idx, target)
        if not target_card:
            return "Nessun bersaglio valido per Ascensione."
        target_card.blessed.append("buff_str:2")
        state.log(f"{player.name} applica Ascensione a {target_card.definition.name} (+2 Forza).")
        return "Ascensione applicata."

    if name_key == _norm("Collasso"):
        target_uid = engine.resolve_target_artifact_or_building(opponent_idx, target)
        if not target_uid:
            return "Bersaglio non valido per Collasso (usa r1-r4 o b)."
        target_card = state.instances[target_uid]
        engine.send_to_graveyard(opponent_idx, target_uid)
        state.log(f"{player.name} distrugge {target_card.definition.name} con Collasso.")
        return "Collasso risolta."

    if name_key == _norm("Dono di Kah"):
        drawn = engine.draw_cards(player_idx, 2)
        state.log(f"{player.name} usa Dono di Kah e pesca {drawn} carte.")
        return "Dono di Kah risolta."

    # Norrena
    if name_key == _norm("Bifrost"):
        target_card = engine.resolve_target_saint(opponent_idx, target)
        if not target_card:
            return "Bersaglio non valido per Bifrost."
        faith = max(0, target_card.definition.faith or 0)
        engine.destroy_saint_by_uid(opponent_idx, target_card.uid, excommunicate=True)
        engine.gain_sin(opponent_idx, faith)
        state.log(f"{player.name} usa Bifrost: scomunica {target_card.definition.name} e infligge {faith} Peccato.")
        return "Bifrost risolta."

    if name_key == _norm("Ragnarok"):
        own_destroyed = 0
        to_destroy = []
        for idx in (0, 1):
            to_destroy.extend((idx, s_uid) for s_uid in engine.all_saints_on_field(idx))
        for owner_idx, s_uid in to_destroy:
            if owner_idx == player_idx:
                own_destroyed += 1
            engine.destroy_saint_by_uid(owner_idx, s_uid)
        engine.draw_cards(player_idx, own_destroyed)
        for name in ("Fenrir", "Jormungandr"):
            summon_uid = None
            for h_uid in list(player.hand):
                if _norm(state.instances[h_uid].definition.name) == _norm(name):
                    summon_uid = h_uid
                    player.hand.remove(h_uid)
                    break
            if summon_uid is None:
                continue
            open_slot = _first_open_slot(engine, player_idx)
            if open_slot:
                zone, slot = open_slot
                engine.place_card_from_uid(player_idx, summon_uid, zone, slot)
                state.log(f"{player.name} evoca {name} con Ragnarok.")
                break
        return "Ragnarok risolta."

    if name_key == _norm("Assalto Invernale"):
        saint_grave = sum(
            1 for g_uid in player.graveyard if _norm(state.instances[g_uid].definition.card_type) == "santo"
        )
        if saint_grave < 3:
            return "Condizione non soddisfatta per Assalto Invernale (servono 3 santi nel cimitero)."
        for summon_name in ("Fenrir", "Jormungandr"):
            found = engine.find_card_uid_in_deck(player_idx, summon_name)
            source = "reliquiario"
            if found is None:
                found = engine.find_card_uid_in_graveyard(player_idx, summon_name)
                source = "cimitero"
            if found is None:
                continue
            if source == "reliquiario":
                player.deck.remove(found)
            else:
                player.graveyard.remove(found)
            slot = _first_open_slot(engine, player_idx)
            if not slot:
                player.graveyard.append(found)
                return "Nessuno slot libero per Assalto Invernale."
            zone, idx = slot
            engine.place_card_from_uid(player_idx, found, zone, idx)
            state.log(f"{player.name} evoca {summon_name} con Assalto Invernale.")
            return "Assalto Invernale risolta."
        return "Nessun Fenrir/Jormungandr disponibile."

    # Animismo
    if name_key == _norm("Fioritura Primaverile"):
        boosted = 0
        for s_uid in engine.all_saints_on_field(player_idx):
            inst = state.instances[s_uid]
            if inst.definition.expansion != "ANI-1":
                continue
            inst.current_faith = (inst.current_faith or 0) + 2
            inst.blessed.append("buff_str:2")
            boosted += 1
        return f"Fioritura Primaverile risolta: {boosted} santi potenziati."

    if name_key == _norm("Legame Primordiale"):
        albero_count = sum(
            1
            for s_uid in engine.all_saints_on_field(player_idx)
            if "albero" in _norm(state.instances[s_uid].definition.name)
        )
        moved = 0
        for g_uid in list(player.graveyard):
            if moved >= albero_count:
                break
            g = state.instances[g_uid]
            if _norm(g.definition.card_type) != "santo":
                continue
            cv = _cross_value(g.definition.crosses)
            if cv is None or cv > 7:
                continue
            player.graveyard.remove(g_uid)
            player.deck.insert(0, g_uid)
            moved += 1
        return f"Legame Primordiale risolta: {moved} carte spostate al reliquiario."

    if name_key == _norm("Memoria della Pietra"):
        for g_uid in list(player.graveyard):
            if "pietra" not in _norm(state.instances[g_uid].definition.name):
                continue
            slot = _first_open_slot(engine, player_idx)
            if not slot:
                return "Nessuno slot libero per Memoria della Pietra."
            player.graveyard.remove(g_uid)
            zone, idx = slot
            engine.place_card_from_uid(player_idx, g_uid, zone, idx)
            return f"Memoria della Pietra risolta: evocata {state.instances[g_uid].definition.name}."
        return "Nessuna carta Pietra nel cimitero."

    if name_key == _norm("Pietra Bianca"):
        target_card = engine.resolve_target_saint(player_idx, target)
        if not target_card:
            return "Bersaglio non valido per Pietra Bianca."
        amount = engine.get_effective_strength(target_card.uid)
        engine.reduce_sin(player_idx, amount)
        return f"Pietra Bianca risolta: -{amount} Peccato."

    if name_key == _norm("Pioggia"):
        healed = 0
        for s_uid in engine.all_saints_on_field(player_idx):
            inst = state.instances[s_uid]
            max_f = inst.definition.faith or 0
            if (inst.current_faith or 0) < max_f:
                inst.current_faith = (inst.current_faith or 0) + 4
                healed += 1
        return f"Pioggia risolta: {healed} santi curati."

    if name_key == _norm("Spore"):
        for h_uid in list(player.hand):
            player.hand.remove(h_uid)
            player.deck.insert(0, h_uid)
        pending = state.flags.setdefault("spore_pending", {"0": False, "1": False})
        pending[str(player_idx)] = True
        return "Spore risolta: mano rimessa nel reliquiario, prossima pescata a 8 carte."

    if name_key == _norm("Tifone"):
        drawn = engine.draw_cards(player_idx, 2)
        milled = 0
        for _ in range(2):
            if not opponent.deck:
                break
            top = opponent.deck.pop()
            opponent.graveyard.append(top)
            milled += 1
        return f"Tifone risolta: peschi {drawn}, avversario manda {milled} carte al cimitero."

    if name_key == _norm("Diboscamento"):
        moved = 0
        for d_uid in list(player.deck):
            if moved >= 3:
                break
            if "albero" not in _norm(state.instances[d_uid].definition.name):
                continue
            player.deck.remove(d_uid)
            player.graveyard.append(d_uid)
            moved += 1
        return f"Diboscamento risolta: {moved} carte Albero mandate al cimitero."

    if name_key == _norm("Colori d'Autunno"):
        destroyed = 0
        for s_uid in list(engine.all_saints_on_field(player_idx)):
            if "albero" not in _norm(state.instances[s_uid].definition.name):
                continue
            engine.destroy_saint_by_uid(player_idx, s_uid)
            engine.gain_sin(player_idx, 2)
            destroyed += 1
        summoned = 0
        for _ in range(destroyed):
            found = None
            for h_uid in list(player.hand):
                if _norm(state.instances[h_uid].definition.name) == _norm("Segno Del Passato"):
                    found = h_uid
                    player.hand.remove(h_uid)
                    break
            if found is None:
                found = engine.find_card_uid_in_deck(player_idx, "Segno Del Passato")
                if found:
                    player.deck.remove(found)
            if found is None:
                continue
            slot = next((i for i, v in enumerate(player.artifacts) if v is None), None)
            if slot is None:
                player.graveyard.append(found)
                continue
            player.artifacts[slot] = found
            summoned += 1
        return f"Colori d'Autunno risolta: {destroyed} Alberi distrutti, {summoned} Segno del Passato evocati."

    if name_key == _norm("Pioggia Acida"):
        for idx in (0, 1):
            for s_uid in list(engine.all_saints_on_field(idx)):
                _damage_saint(engine, s_uid, 2)
        return "Pioggia Acida risolta."

    if name_key == _norm("Pietre Pesanti"):
        flags = state.flags.setdefault("double_cost_turns", {"0": 0, "1": 0})
        flags[str(opponent_idx)] = int(flags.get(str(opponent_idx), 0)) + 1
        return "Pietre Pesanti risolta: costo Ispirazione avversario raddoppiato nel prossimo turno."

    if name_key == _norm("Proibizione Naturale"):
        target_card = engine.resolve_target_saint(opponent_idx, target)
        if not target_card:
            return "Bersaglio non valido per Proibizione Naturale."
        target_card.cursed.append("silenced")
        return f"Proibizione Naturale risolta su {target_card.definition.name}."

    if name_key == _norm("Tempesta"):
        for s_uid in list(engine.all_saints_on_field(opponent_idx)):
            _damage_saint(engine, s_uid, 3)
        return "Tempesta risolta."

    if name_key == _norm("Voragine"):
        target_card = engine.resolve_target_saint(opponent_idx, target)
        if not target_card:
            return "Bersaglio non valido per Voragine."
        engine.destroy_saint_by_uid(opponent_idx, target_card.uid)
        return "Voragine risolta."

    if name_key == _norm("Uragano"):
        saint_target = None
        artifact_target = None
        if target and "," in target:
            left, right = [x.strip() for x in target.split(",", 1)]
            saint_target = engine.resolve_target_saint(opponent_idx, left)
            artifact_target = engine.resolve_target_artifact_or_building(opponent_idx, right)
        else:
            saint_target = engine.resolve_target_saint(opponent_idx, target)
            artifact_target = engine.resolve_target_artifact_or_building(opponent_idx, "r1")
        if saint_target:
            engine.destroy_saint_by_uid(opponent_idx, saint_target.uid)
        if artifact_target:
            engine.send_to_graveyard(opponent_idx, artifact_target)
        return "Uragano risolta."

    if name_key == _norm("Terremoto: Magnitudo 3"):
        t_uid = engine.resolve_target_artifact_or_building(opponent_idx, target)
        if not t_uid:
            return "Bersaglio non valido per Magnitudo 3."
        engine.send_to_graveyard(opponent_idx, t_uid)
        engine.gain_sin(player_idx, 2)
        return "Terremoto Magnitudo 3 risolta."

    if name_key == _norm("Terremoto: Magnitudo 10"):
        destroyed = 0
        for idx in (0, 1):
            p = state.players[idx]
            for a_uid in list(p.artifacts):
                if a_uid:
                    engine.send_to_graveyard(idx, a_uid)
                    destroyed += 1
            if p.building:
                engine.send_to_graveyard(idx, p.building)
                destroyed += 1
        sin_gain = 2 * destroyed
        engine.gain_sin(0, sin_gain)
        engine.gain_sin(1, sin_gain)
        for h_uid in list(player.hand):
            if _norm(state.instances[h_uid].definition.name) == _norm("Vulcano"):
                slot = _first_open_slot(engine, player_idx)
                if slot:
                    player.hand.remove(h_uid)
                    z, s = slot
                    engine.place_card_from_uid(player_idx, h_uid, z, s)
                    state.log(f"{player.name} evoca Vulcano per effetto di Magnitudo 10.")
                break
        return "Terremoto Magnitudo 10 risolta."

    if name_key == _norm("Monsone"):
        discard_selected: list[str] = []
        return_selected: list[str] = []
        raw = (target or "").strip()
        if raw.startswith("monsone:"):
            body = raw[len("monsone:") :]
            for part in body.split(";"):
                part = part.strip()
                if "=" not in part:
                    continue
                key, val = part.split("=", 1)
                key = _norm(key)
                vals = [v.strip() for v in val.split(",") if v.strip()]
                if key == "discard":
                    discard_selected.extend(vals)
                elif key == "return":
                    return_selected.extend(vals)

        moved = 0
        for h_uid in discard_selected[:3]:
            if h_uid in player.hand:
                player.hand.remove(h_uid)
                player.graveyard.append(h_uid)
                moved += 1
        while moved < 3 and player.deck:
            uid_d = player.deck.pop()
            player.graveyard.append(uid_d)
            moved += 1

        returned = 0
        used: set[str] = set()
        if return_selected:
            for f_uid in return_selected:
                if returned >= 3 or f_uid in used:
                    continue
                used.add(f_uid)
                owner_idx = None
                for idx in (0, 1):
                    p = state.players[idx]
                    if f_uid in (p.attack + p.defense + p.artifacts) or p.building == f_uid:
                        owner_idx = idx
                        break
                if owner_idx is None:
                    continue
                cv = _cross_value(state.instances[f_uid].definition.crosses)
                if cv is None or cv > 8:
                    continue
                engine._remove_from_board(state.players[owner_idx], f_uid)
                state.players[owner_idx].deck.insert(0, f_uid)
                returned += 1
        else:
            for owner_idx, f_uid in list(_iter_all_field_cards(engine)):
                if returned >= 3:
                    break
                cv = _cross_value(state.instances[f_uid].definition.crosses)
                if cv is None or cv > 8:
                    continue
                state.players[owner_idx].deck.insert(0, f_uid)
                engine._remove_from_board(state.players[owner_idx], f_uid)
                returned += 1

        engine.rng.shuffle(state.players[0].deck)
        engine.rng.shuffle(state.players[1].deck)
        return f"Monsone risolta: {moved} carte mandate al cimitero, {returned} carte rimesse nei reliquiari."

    if name_key == _norm("Inverno"):
        done = 0
        for owner_idx, f_uid in list(_iter_all_field_cards(engine)):
            if done >= 3:
                break
            cv = _cross_value(state.instances[f_uid].definition.crosses)
            if cv is None or cv > 8:
                continue
            engine.excommunicate_card(owner_idx, f_uid)
            done += 1
        return f"Inverno risolta: {done} carte scomunicate."

    if name_key == _norm("Tornado"):
        target_saint = engine.resolve_target_saint(opponent_idx, target)
        keep_uid = target_saint.uid if target_saint else None
        for idx in (0, 1):
            for s_uid in list(engine.all_saints_on_field(idx)):
                if s_uid == keep_uid:
                    continue
                engine.destroy_saint_by_uid(idx, s_uid)
        return "Tornado risolta."

    if name_key == _norm("Sacrificio Naturale"):
        if any(uid is not None for uid in opponent.defense):
            return "Sacrificio Naturale non valida: l'avversario ha santi in difesa."
        summoned = 0
        for _ in range(3):
            found = None
            for h_uid in list(player.hand):
                if _norm(state.instances[h_uid].definition.name) == _norm("Token Sacrificale"):
                    found = h_uid
                    player.hand.remove(h_uid)
                    break
            if found is None:
                found = engine.find_card_uid_in_deck(player_idx, "Token Sacrificale")
                if found:
                    player.deck.remove(found)
            if found is None:
                break
            free = engine.empty_slots(opponent_idx, "defense")
            if not free:
                player.graveyard.append(found)
                break
            opponent.defense[free[0]] = found
            summoned += 1
        return f"Sacrificio Naturale risolta: {summoned} Token Sacrificali evocati."

    generic = _resolve_generic_text_effect(engine, player_idx, uid, target)
    if generic is not None:
        return generic
    state.log(f"{player.name} usa {card.definition.name}: effetto registrato ma senza risoluzione automatica.")
    return f"{card.definition.name}: effetto registrato (risoluzione avanzata in sviluppo)."


def resolve_activated_effect(engine: "GameEngine", player_idx: int, uid: str, target: str | None) -> str:
    state = engine.state
    player = state.players[player_idx]
    card = state.instances[uid]
    text = _norm(card.definition.effect_text or "")
    raw_text = card.definition.effect_text or ""

    if not engine.can_activate_once_per_turn(uid) and "una volta per turno" in text:
        return f"{card.definition.name}: abilita gia usata in questo turno."

    acted = False
    logs: list[str] = []

    if _norm(card.definition.name) == _norm("Sacerdote Orologio"):
        opp_idx = 1 - player_idx
        chosen = engine.resolve_target_saint(opp_idx, target) if target else None
        if chosen is None:
            for s_uid in engine.all_saints_on_field(opp_idx):
                cand = state.instances[s_uid]
                cv = _cross_value(cand.definition.crosses)
                if cv is None or cv > 5:
                    continue
                if (cand.current_faith or 0) >= (cand.definition.faith or 0):
                    continue
                chosen = cand
                break
        if chosen is None:
            return "Sacerdote Orologio: nessun bersaglio valido (serve santo avversario danneggiato con Croci <= 5)."
        cv = _cross_value(chosen.definition.crosses)
        if cv is None or cv > 5 or (chosen.current_faith or 0) >= (chosen.definition.faith or 0):
            return "Sacerdote Orologio: bersaglio non valido (serve santo avversario danneggiato con Croci <= 5)."
        card.blessed = [t for t in card.blessed if not t.startswith("orologio_link:")]
        card.blessed.append(f"orologio_link:{chosen.uid}")
        msg = f"{player.name} collega Sacerdote Orologio a {chosen.definition.name}."
        state.log(msg)
        return msg

    if _norm(card.definition.name) == _norm("Campana"):
        current = 0
        for tag in list(card.blessed):
            if tag.startswith("campana_counter:"):
                try:
                    current = int(tag.split(":", 1)[1])
                except ValueError:
                    current = 0
                card.blessed.remove(tag)
        if current <= 0:
            return "Campana: nessun segnalino disponibile."
        use = current
        if target and target.isdigit():
            use = max(1, min(current, int(target)))
        if player.inspiration < use:
            card.blessed.append(f"campana_counter:{current}")
            return "Campana: Ispirazione insufficiente."
        player.inspiration -= use
        rem = current - use
        if rem > 0:
            card.blessed.append(f"campana_counter:{rem}")
        for s_uid in engine.all_saints_on_field(player_idx):
            s = state.instances[s_uid]
            s.current_faith = (s.current_faith or 0) + use
        acted = True
        logs.append(f"Campana consuma {use} segnalini e potenzia i tuoi santi di +{use} Fede.")

    if "manda questa carta dal terreno al cimitero" in text:
        engine.remove_from_board_no_sin(player_idx, uid)
        acted = True
        logs.append(f"{card.definition.name} viene mandato al cimitero senza peccato.")

    if "evocare" in text and ("dalla tua mano" in text or "dal tuo cimitero" in text or "dal reliquiario" in text):
        quoted = _extract_quoted_names(raw_text)
        chosen_uid = None
        source = ""
        # Priority: target by name in hand, then graveyard, then deck.
        if "dalla tua mano" in text:
            for h_uid in list(player.hand):
                if not quoted or _norm(state.instances[h_uid].definition.name) in {_norm(q) for q in quoted}:
                    chosen_uid = h_uid
                    source = "hand"
                    break
        if chosen_uid is None and "dal tuo cimitero" in text:
            for g_uid in list(player.graveyard):
                if not quoted or _norm(state.instances[g_uid].definition.name) in {_norm(q) for q in quoted}:
                    chosen_uid = g_uid
                    source = "graveyard"
                    break
        if chosen_uid is None and "dal reliquiario" in text:
            for d_uid in list(player.deck):
                if not quoted or _norm(state.instances[d_uid].definition.name) in {_norm(q) for q in quoted}:
                    chosen_uid = d_uid
                    source = "deck"
                    break
        if chosen_uid:
            if source == "hand":
                player.hand.remove(chosen_uid)
            elif source == "graveyard":
                player.graveyard.remove(chosen_uid)
            elif source == "deck":
                player.deck.remove(chosen_uid)
            if _summon_uid_to_first_slot(engine, player_idx, chosen_uid):
                acted = True
                logs.append(f"{player.name} evoca {state.instances[chosen_uid].definition.name}.")
            else:
                # Rollback minimal.
                if source == "hand":
                    player.hand.append(chosen_uid)
                elif source == "graveyard":
                    player.graveyard.append(chosen_uid)
                else:
                    player.deck.insert(0, chosen_uid)

    if "riprendi dal tuo cimitero un artefatto e aggiungilo alla tua mano" in text:
        for g_uid in list(player.graveyard):
            if _norm(state.instances[g_uid].definition.card_type) == "artefatto":
                if engine.move_graveyard_card_to_hand(player_idx, g_uid):
                    acted = True
                    logs.append(f"{player.name} riprende {state.instances[g_uid].definition.name} dal cimitero.")
                break

    if "se controlli almeno 3 santi con nomi diversi, pesca una carta" in text:
        names = {_norm(state.instances[s_uid].definition.name) for s_uid in engine.all_saints_on_field(player_idx)}
        if len(names) >= 3:
            drawn = engine.draw_cards(player_idx, 1)
            acted = True
            logs.append(f"{player.name} pesca {drawn} carta.")

    if acted:
        if "una volta per turno" in text:
            engine.mark_activated_this_turn(uid)
        msg = f"{player.name} attiva {card.definition.name}: {' '.join(logs)}"
        state.log(msg)
        return msg
    return f"{card.definition.name}: abilita non disponibile."
