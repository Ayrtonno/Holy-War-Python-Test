from __future__ import annotations

import argparse
import random
import time
from pathlib import Path

from holywar.app_paths import bundled_data_dir
from holywar.ai.simple_ai import choose_action
from holywar.core.engine import GameEngine
from holywar.core.state import GameState
from holywar.data.deck_builder import (
    available_premade_decks,
    available_religions,
    export_test_decks,
    export_premades_json,
    get_premade_label,
    register_premades_from_json,
)
from holywar.data.importer import load_cards_from_xlsx, write_cards_json, load_cards_json


DEFAULT_JSON = bundled_data_dir() / "cards.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Holy War - MVP terminale")
    parser.add_argument("--deck-xlsx", type=str, default=None, help="Percorso a Holy War.xlsx")
    parser.add_argument("--cards-json", type=str, default=str(DEFAULT_JSON), help="Cache JSON carte")
    parser.add_argument("--load", type=str, default=None, help="Carica partita da file JSON")
    parser.add_argument("--export-test-decks", type=str, default=None, help="Esporta deck test JSON per religione")
    parser.add_argument("--premades-json", type=str, default=None, help="Importa deck premade custom da JSON")
    parser.add_argument("--export-premades-json", type=str, default=None, help="Esporta deck premade in JSON")
    parser.add_argument("--seed", type=int, default=None, help="Seed RNG (se omesso: casuale ad ogni partita)")
    parser.add_argument("--ai-delay", type=float, default=1.2, help="Secondi di pausa tra azioni AI")
    return parser


def ensure_cards(args: argparse.Namespace):
    json_path = Path(args.cards_json)
    if args.deck_xlsx:
        cards = load_cards_from_xlsx(args.deck_xlsx)
        write_cards_json(cards, json_path)
        return cards
    if json_path.exists():
        return load_cards_json(json_path)
    raise SystemExit("Serve --deck-xlsx almeno al primo avvio per generare il JSON carte.")


def print_state(engine: GameEngine) -> None:
    st = engine.state
    print("\n" + "=" * 70)
    print(
        f"Fase: {st.phase} | Turno {st.turn_number} | Giocatore attivo: {st.players[st.active_player].name}"
    )
    for i, p in enumerate(st.players):
        marker = "*" if i == st.active_player else " "
        print(
            f"{marker} {p.name} | Peccato={p.sin}/100 | Ispirazione={p.inspiration} | Mano={len(p.hand)} | Deck={len(p.deck)}"
        )
        print("  Attacco:", _fmt_slots(engine, p.attack))
        print("  Difesa :", _fmt_slots(engine, p.defense))
        print("  Artef. :", _fmt_slots(engine, p.artifacts))
        print("  Edificio:", _fmt_card(engine, p.building))
    print("=" * 70)


def _fmt_card(engine: GameEngine, uid: str | None) -> str:
    if not uid:
        return "-"
    inst = engine.state.instances[uid]
    faith = f" F:{inst.current_faith}" if inst.current_faith is not None else ""
    strength_val = (
        engine.get_effective_strength(uid)
        if inst.definition.card_type.lower() in {"santo", "token"}
        else inst.definition.strength
    )
    strength = f" P:{strength_val}" if strength_val is not None else ""
    return f"{inst.definition.name}{faith}{strength}"


def _fmt_slots(engine: GameEngine, slots: list[str | None]) -> str:
    return " | ".join(_fmt_card(engine, uid) for uid in slots)


def print_hand(engine: GameEngine, player_idx: int) -> None:
    p = engine.state.players[player_idx]
    print(f"\nMano di {p.name}:")
    for idx, uid in enumerate(p.hand):
        c = engine.state.instances[uid].definition
        cost = c.faith if c.faith is not None else 0
        print(f"  [{idx}] {c.name} ({c.card_type}) costo={cost} croci={c.crosses}")


def choose_expansion(cards, prompt: str) -> str:
    expansions = available_religions(cards)
    print(prompt)
    for i, exp in enumerate(expansions):
        print(f"  [{i}] {exp}")
    while True:
        val = input("> ").strip()
        if val.isdigit() and 0 <= int(val) < len(expansions):
            return expansions[int(val)]
        print("Scelta non valida.")


def choose_premade_for_religion(religion: str, prompt: str) -> str | None:
    decks = available_premade_decks(religion)
    print(prompt)
    print("  [0] Auto (deck test)")
    for i, (deck_id, _, name) in enumerate(decks, 1):
        print(f"  [{i}] {name}")
    while True:
        val = input("> ").strip()
        if val.isdigit():
            idx = int(val)
            if idx == 0:
                return None
            if 1 <= idx <= len(decks):
                return decks[idx - 1][0]
        print("Scelta non valida.")


def prompt_reaction(engine: GameEngine, defender_idx: int) -> None:
    p = engine.state.players[defender_idx]
    while True:
        quick_indexes = []
        for i, uid in enumerate(p.hand):
            inst = engine.state.instances[uid].definition
            t = inst.card_type.lower()
            if t in {"benedizione", "maledizione"} or inst.name.lower().strip() == "moribondo":
                quick_indexes.append(i)
        if not quick_indexes:
            return
        print(f"{p.name}, reazione? (quick <idx> <target> | pass)")
        cmd = input(f"{p.name}> ").strip()
        if cmd == "pass" or cmd == "":
            return
        parts = cmd.split()
        if parts[0] == "quick" and len(parts) >= 2 and parts[1].isdigit():
            idx = int(parts[1])
            target = parts[2] if len(parts) >= 3 else None
            res = engine.quick_play(defender_idx, idx, target)
            print(res.message)
            continue
        print("Comando reazione non valido.")


def run_ai_turn(engine: GameEngine, rng: random.Random, player_idx: int, ai_delay: float) -> None:
    for _ in range(12):
        if engine.state.winner is not None:
            return
        before_logs = len(engine.state.logs)
        result = choose_action(engine, player_idx, rng)
        new_logs = engine.state.logs[before_logs:]
        for line in new_logs:
            print(f"[LOG] {line}")
        # Human can respond with quick effects to each AI action.
        if result.message != "AI passa.":
            prompt_reaction(engine, 0)
        if result.message == "AI passa.":
            print("[LOG] AI passa.")
            break
        if ai_delay > 0:
            time.sleep(ai_delay)
    engine.end_turn()


def run_game(engine: GameEngine, mode: str, seed: int, ai_delay: float) -> None:
    rng = random.Random(seed)
    while engine.state.winner is None:
        active = engine.state.active_player
        player = engine.state.players[active]
        engine.start_turn()

        if mode == "ai" and active == 1:
            run_ai_turn(engine, rng, active, ai_delay)
            continue

        while True:
            if engine.state.winner is not None:
                break
            print_state(engine)
            print_hand(engine, active)
            cmd = input(f"\n{player.name}> ").strip()
            if not cmd:
                continue
            parts = cmd.split()
            op = parts[0].lower()

            if op == "help":
                print("Comandi: state, hand, play <idx> [a1|a2|a3|d1|d2|d3|r1..r4|b], attack <a1..a3|d1..d3> [t1..t3], activate <a1|a2|a3|d1|d2|d3|r1|r2|r3|r4|b> [target], swap <a1..a3> <a1..a3>, quick <idx> [target], save <path>, log <path>, end, quit")
                continue
            if op == "state":
                print_state(engine)
                continue
            if op == "hand":
                print_hand(engine, active)
                continue
            if op == "play" and len(parts) >= 2 and parts[1].isdigit():
                idx = int(parts[1])
                target = parts[2] if len(parts) >= 3 else None
                res = engine.play_card(active, idx, target)
                print(res.message)
                if res.ok and mode == "local":
                    prompt_reaction(engine, 1 - active)
                continue
            if op == "quick" and len(parts) >= 2 and parts[1].isdigit():
                idx = int(parts[1])
                target = parts[2] if len(parts) >= 3 else None
                res = engine.quick_play(active, idx, target)
                print(res.message)
                continue
            if op == "swap" and len(parts) == 3:
                if parts[1].startswith("a") and parts[2].startswith("a"):
                    f = int(parts[1][1]) - 1
                    t = int(parts[2][1]) - 1
                    res = engine.move_attack_positions(active, f, t)
                    print(res.message)
                    continue
            if op == "attack" and len(parts) >= 2:
                source = parts[1].strip().lower()
                from_slot = -99
                if len(source) >= 2 and source[1].isdigit():
                    slot = int(source[1]) - 1
                    if source[0] == "a":
                        from_slot = slot
                    elif source[0] == "d":
                        from_slot = -(slot + 1)
                target_slot = None
                if len(parts) >= 3 and parts[2].startswith("t"):
                    target_slot = int(parts[2][1]) - 1
                res = engine.attack(active, from_slot, target_slot)
                print(res.message)
                if res.ok and mode == "local":
                    prompt_reaction(engine, 1 - active)
                continue
            if op == "activate" and len(parts) >= 2:
                source = parts[1]
                target = parts[2] if len(parts) >= 3 else None
                res = engine.activate_ability(active, source, target)
                print(res.message)
                if res.ok and mode == "local":
                    prompt_reaction(engine, 1 - active)
                continue
            if op == "save" and len(parts) == 2:
                out = engine.state.save(parts[1])
                print(f"Salvato in {out}")
                continue
            if op == "log" and len(parts) == 2:
                out = engine.export_logs(parts[1])
                print(f"Log esportato in {out}")
                continue
            if op == "end":
                engine.end_turn()
                break
            if op == "quit":
                return
            print("Comando non valido. Usa 'help'.")

    winner = engine.state.players[engine.state.winner].name
    print(f"\nPartita terminata. Vincitore: {winner}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.premades_json:
        warns = register_premades_from_json(args.premades_json)
        for w in warns:
            print(f"[WARN PREMADE] {w}")
    if args.export_premades_json:
        out = export_premades_json(args.export_premades_json, include_builtin=True)
        print(f"Premade esportati in {out}")
        return

    if args.load:
        state = GameState.load(args.load)
        engine = GameEngine(state)
        mode = input("Modalita (local/ai)? ").strip().lower() or "local"
        run_game(engine, mode, args.seed, args.ai_delay)
        return

    cards = ensure_cards(args)
    if args.export_test_decks:
        paths = export_test_decks(cards, args.export_test_decks)
        print("Deck test esportati:")
        for p in paths:
            print(f" - {p}")
        return
    print("Seleziona modalita: [0] 1v1 locale, [1] vs AI")
    mode_pick = input("> ").strip()
    mode = "ai" if mode_pick == "1" else "local"

    p1_name = input("Nome Giocatore 1: ").strip() or "Giocatore 1"
    p2_name = "AI" if mode == "ai" else (input("Nome Giocatore 2: ").strip() or "Giocatore 2")

    p1_expansion = choose_expansion(cards, "Espansione Giocatore 1:")
    p2_expansion = choose_expansion(cards, "Espansione Giocatore 2:")
    print("Selezione deck: [0] Auto test deck, [1] Deck premade")
    deck_mode = input("> ").strip()
    p1_premade = None
    p2_premade = None
    if deck_mode == "1":
        p1_premade = choose_premade_for_religion(p1_expansion, f"Deck premade per {p1_name}:")
        p2_premade = choose_premade_for_religion(p2_expansion, f"Deck premade per {p2_name}:")
        if p1_premade:
            print(f"{p1_name} usa: {get_premade_label(p1_premade)}")
        if p2_premade:
            print(f"{p2_name} usa: {get_premade_label(p2_premade)}")

    engine = GameEngine.create_new(
        cards=cards,
        p1_name=p1_name,
        p2_name=p2_name,
        p1_expansion=p1_expansion,
        p2_expansion=p2_expansion,
        p1_premade_deck_id=p1_premade,
        p2_premade_deck_id=p2_premade,
        seed=args.seed,
    )
    run_game(engine, mode, args.seed, args.ai_delay)


if __name__ == "__main__":
    main()
