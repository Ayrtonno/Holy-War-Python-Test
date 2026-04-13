from __future__ import annotations

import argparse
import random
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from holywar.ai.simple_ai import choose_action
from holywar.cli import ensure_cards
from holywar.core.engine import GameEngine
from holywar.data.deck_builder import (
    available_premade_decks,
    available_religions,
    get_premade_label,
    register_premades_from_json,
)


class HolyWarGUI(tk.Tk):
    def __init__(self, cards, seed: int | None, ai_delay: float) -> None:
        super().__init__()
        self.title("Holy War - GUI MVP")
        self.geometry("1280x860")
        self.cards = cards
        self.seed = seed
        self.ai_delay_ms = max(0, int(ai_delay * 1000))
        self.rng = random.Random(seed)
        self.mode_var = tk.StringVar(value="ai")
        self.p1_name_var = tk.StringVar(value="Giocatore")
        self.p2_name_var = tk.StringVar(value="AI")
        religions = available_religions(cards)
        self.p1_rel_var = tk.StringVar(value=religions[0] if religions else "Animismo")
        self.p2_rel_var = tk.StringVar(value=religions[1] if len(religions) > 1 else self.p1_rel_var.get())
        self.p1_deck_var = tk.StringVar(value="AUTO (test)")
        self.p2_deck_var = tk.StringVar(value="AUTO (test)")
        self.chain_enabled = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="Pronto")
        self.engine: GameEngine | None = None
        self.last_log_idx = 0
        self.turn_started = False
        self.ai_running = False
        self.chain_active = False
        self.chain_priority_idx = 0
        self.chain_pass_count = 0
        self.religions = religions
        self._p1_deck_map: dict[str, str | None] = {}
        self._p2_deck_map: dict[str, str | None] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=8)

        ttk.Label(top, text="Modalita").grid(row=0, column=0, sticky="w")
        ttk.Combobox(top, textvariable=self.mode_var, values=["ai", "local"], width=8, state="readonly").grid(row=0, column=1, padx=4, sticky="ew")
        ttk.Label(top, text="P1").grid(row=0, column=2)
        ttk.Entry(top, textvariable=self.p1_name_var, width=12).grid(row=0, column=3, padx=4, sticky="ew")
        ttk.Label(top, text="Religione P1").grid(row=0, column=4)
        self.p1_rel_combo = ttk.Combobox(top, textvariable=self.p1_rel_var, values=self.religions, width=16, state="readonly")
        self.p1_rel_combo.grid(row=0, column=5, padx=4, sticky="ew")
        ttk.Label(top, text="Deck P1").grid(row=0, column=6)
        self.p1_deck_combo = ttk.Combobox(top, textvariable=self.p1_deck_var, values=["AUTO (test)"], width=28, state="readonly")
        self.p1_deck_combo.grid(row=0, column=7, padx=4, sticky="ew")
        ttk.Label(top, text="P2").grid(row=0, column=8)
        ttk.Entry(top, textvariable=self.p2_name_var, width=12).grid(row=0, column=9, padx=4, sticky="ew")
        ttk.Label(top, text="Religione P2").grid(row=0, column=10)
        self.p2_rel_combo = ttk.Combobox(top, textvariable=self.p2_rel_var, values=self.religions, width=16, state="readonly")
        self.p2_rel_combo.grid(row=0, column=11, padx=4, sticky="ew")
        ttk.Label(top, text="Deck P2").grid(row=0, column=12)
        self.p2_deck_combo = ttk.Combobox(top, textvariable=self.p2_deck_var, values=["AUTO (test)"], width=28, state="readonly")
        self.p2_deck_combo.grid(row=0, column=13, padx=4, sticky="ew")

        actions = ttk.Frame(top)
        actions.grid(row=1, column=0, columnspan=14, sticky="w", pady=(6, 0))
        ttk.Button(actions, text="Nuova Partita", command=self.new_game).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Fine Turno", command=self.end_turn).pack(side="left", padx=4)
        ttk.Button(actions, text="Salva", command=self.save_game).pack(side="left", padx=4)
        ttk.Button(actions, text="Esporta Log", command=self.export_log).pack(side="left", padx=4)
        ttk.Button(actions, text="Catena SI", command=lambda: self.set_chain_enabled(True)).pack(side="left", padx=(12, 4))
        ttk.Button(actions, text="Catena NO", command=lambda: self.set_chain_enabled(False)).pack(side="left", padx=4)
        ttk.Button(actions, text="OK Catena", command=self.chain_ok).pack(side="left", padx=4)

        top.columnconfigure(7, weight=1)
        top.columnconfigure(13, weight=1)
        self.p1_rel_combo.bind("<<ComboboxSelected>>", lambda _e: self.update_premade_options())
        self.p2_rel_combo.bind("<<ComboboxSelected>>", lambda _e: self.update_premade_options())
        self.update_premade_options()

        ttk.Label(self, textvariable=self.status_var).pack(fill="x", padx=8)

        center = ttk.Frame(self)
        center.pack(fill="both", expand=True, padx=8, pady=8)

        board = ttk.Frame(center)
        board.pack(side="left", fill="both", expand=True)

        self.info_label = ttk.Label(board, text="Nessuna partita")
        self.info_label.pack(anchor="w", pady=4)

        enemy_frame = ttk.LabelFrame(board, text="Campo Avversario")
        enemy_frame.pack(fill="x", pady=4)
        self.enemy_attack = [ttk.Label(enemy_frame, text="-", width=24) for _ in range(3)]
        self.enemy_defense = [ttk.Label(enemy_frame, text="-", width=24) for _ in range(3)]
        self.enemy_artifacts = [ttk.Label(enemy_frame, text="-", width=24) for _ in range(4)]
        self.enemy_building = ttk.Label(enemy_frame, text="-", width=24)
        self._grid_slots(enemy_frame, self.enemy_attack, self.enemy_defense, self.enemy_artifacts, self.enemy_building)

        own_frame = ttk.LabelFrame(board, text="Il Tuo Campo")
        own_frame.pack(fill="x", pady=4)
        self.own_attack = [tk.Button(own_frame, text="-", width=24) for _ in range(3)]
        self.own_defense = [tk.Button(own_frame, text="-", width=24) for _ in range(3)]
        self.own_artifacts = [tk.Button(own_frame, text="-", width=24) for _ in range(4)]
        self.own_building = tk.Button(own_frame, text="-", width=24)
        self._grid_slots(own_frame, self.own_attack, self.own_defense, self.own_artifacts, self.own_building)

        for i, btn in enumerate(self.own_attack):
            btn.bind("<Button-3>", lambda e, idx=i: self.on_own_slot_right_click(f"a{idx + 1}"))
            btn.bind("<Button-1>", lambda e, idx=i: self.show_board_card_detail(0, "attack", idx))
        for i, btn in enumerate(self.own_defense):
            btn.bind("<Button-3>", lambda e, idx=i: self.on_own_slot_right_click(f"d{idx + 1}"))
            btn.bind("<Button-1>", lambda e, idx=i: self.show_board_card_detail(0, "defense", idx))
        for i, btn in enumerate(self.own_artifacts):
            btn.bind("<Button-3>", lambda e, idx=i: self.on_own_slot_right_click(f"r{idx + 1}"))
            btn.bind("<Button-1>", lambda e, idx=i: self.show_board_card_detail(0, "artifacts", idx))
        self.own_building.bind("<Button-3>", lambda e: self.on_own_slot_right_click("b"))
        self.own_building.bind("<Button-1>", lambda e: self.show_board_card_detail(0, "building", 0))
        for i, lbl in enumerate(self.enemy_attack):
            lbl.bind("<Button-1>", lambda e, idx=i: self.show_board_card_detail(1, "attack", idx))
        for i, lbl in enumerate(self.enemy_defense):
            lbl.bind("<Button-1>", lambda e, idx=i: self.show_board_card_detail(1, "defense", idx))
        for i, lbl in enumerate(self.enemy_artifacts):
            lbl.bind("<Button-1>", lambda e, idx=i: self.show_board_card_detail(1, "artifacts", idx))
        self.enemy_building.bind("<Button-1>", lambda e: self.show_board_card_detail(1, "building", 0))

        hand_frame = ttk.LabelFrame(board, text="Mano (tasto destro su carta)")
        hand_frame.pack(fill="both", expand=True, pady=4)
        self.hand_list = tk.Listbox(hand_frame, height=12)
        self.hand_list.pack(fill="both", expand=True, side="left")
        scroll = ttk.Scrollbar(hand_frame, command=self.hand_list.yview)
        self.hand_list.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.hand_list.bind("<Button-3>", self.on_hand_right_click)
        self.hand_list.bind("<<ListboxSelect>>", self.on_hand_select)

        detail_frame = ttk.LabelFrame(board, text="Dettaglio Carta")
        detail_frame.pack(fill="both", expand=True, pady=4)
        self.card_detail_text = tk.Text(detail_frame, wrap="word", height=9)
        self.card_detail_text.pack(fill="both", expand=True)
        self.card_detail_text.configure(state="disabled")

        log_frame = ttk.LabelFrame(center, text="Log Partita")
        log_frame.pack(side="right", fill="both", expand=True)
        self.log_text = tk.Text(log_frame, wrap="word", width=58)
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")

    def _grid_slots(self, parent, attack, defense, artifacts, building) -> None:
        ttk.Label(parent, text="Attacco").grid(row=0, column=0, sticky="w")
        for i, w in enumerate(attack):
            w.grid(row=1, column=i, padx=2, pady=2)
        ttk.Label(parent, text="Difesa").grid(row=2, column=0, sticky="w")
        for i, w in enumerate(defense):
            w.grid(row=3, column=i, padx=2, pady=2)
        ttk.Label(parent, text="Artefatti").grid(row=4, column=0, sticky="w")
        for i, w in enumerate(artifacts):
            w.grid(row=5, column=i, padx=2, pady=2)
        ttk.Label(parent, text="Edificio").grid(row=6, column=0, sticky="w")
        building.grid(row=7, column=0, padx=2, pady=2)

    def update_premade_options(self) -> None:
        def build_map(religion: str) -> dict[str, str | None]:
            out: dict[str, str | None] = {"AUTO (test)": None}
            for deck_id, _, _name in available_premade_decks(religion):
                out[get_premade_label(deck_id)] = deck_id
            return out

        self._p1_deck_map = build_map(self.p1_rel_var.get())
        self._p2_deck_map = build_map(self.p2_rel_var.get())
        p1_vals = list(self._p1_deck_map.keys())
        p2_vals = list(self._p2_deck_map.keys())
        self.p1_deck_combo.configure(values=p1_vals)
        self.p2_deck_combo.configure(values=p2_vals)
        if self.p1_deck_var.get() not in self._p1_deck_map:
            self.p1_deck_var.set("AUTO (test)")
        if self.p2_deck_var.get() not in self._p2_deck_map:
            self.p2_deck_var.set("AUTO (test)")

    def new_game(self) -> None:
        mode = self.mode_var.get().strip().lower()
        p1 = self.p1_name_var.get().strip() or "Giocatore"
        p2 = self.p2_name_var.get().strip() or ("AI" if mode == "ai" else "Giocatore 2")
        if mode == "ai":
            p2 = "AI"
            self.p2_name_var.set("AI")
        self.update_premade_options()
        p1_deck_id = self._p1_deck_map.get(self.p1_deck_var.get())
        p2_deck_id = self._p2_deck_map.get(self.p2_deck_var.get())
        self.engine = GameEngine.create_new(
            cards=self.cards,
            p1_name=p1,
            p2_name=p2,
            p1_expansion=self.p1_rel_var.get(),
            p2_expansion=self.p2_rel_var.get(),
            p1_premade_deck_id=p1_deck_id,
            p2_premade_deck_id=p2_deck_id,
            seed=self.seed,
        )
        self.rng = random.Random(self.seed)
        self.last_log_idx = 0
        self.turn_started = False
        self.ai_running = False
        self.chain_active = False
        self.chain_priority_idx = 0
        self.chain_pass_count = 0
        self.status_var.set("Partita avviata")
        self.refresh()
        self.begin_turn_if_needed()

    def current_human_idx(self) -> int | None:
        if self.engine is None:
            return None
        if self.chain_active:
            return self.chain_priority_idx
        if self.mode_var.get() == "ai":
            return 0
        return self.engine.state.active_player

    def can_human_act(self) -> bool:
        if self.engine is None or self.engine.state.winner is not None:
            return False
        if self.chain_active:
            if self.mode_var.get() == "ai":
                return self.chain_priority_idx == 0
            return True
        if self.ai_running:
            return False
        if self.mode_var.get() == "ai" and self.engine.state.active_player == 1:
            return False
        return True

    def begin_turn_if_needed(self) -> None:
        if self.engine is None or self.ai_running:
            return
        if not self.turn_started and self.engine.state.winner is None:
            self.engine.start_turn()
            self.turn_started = True
            self.refresh()
        if self.mode_var.get() == "ai" and self.engine and self.engine.state.active_player == 1 and not self.ai_running:
            self.start_ai_turn()

    def start_ai_turn(self) -> None:
        self.ai_running = True
        self._ai_steps = 0
        self.after(max(50, self.ai_delay_ms), self.ai_step)

    def ai_step(self) -> None:
        if self.engine is None:
            self.ai_running = False
            return
        if self.engine.state.winner is not None or self.engine.state.active_player != 1:
            self.ai_running = False
            self.refresh()
            return
        self._ai_steps += 1
        result = choose_action(self.engine, 1, self.rng)
        if result.ok and result.message != "AI passa.":
            self.start_chain(actor_idx=1)
            self.refresh()
            if self.chain_active:
                # Pause AI turn until chain resolves.
                return
        self.refresh()
        if result.message == "AI passa." or self._ai_steps >= 12:
            self.engine.end_turn()
            self.turn_started = False
            self.ai_running = False
            self.refresh()
            self.begin_turn_if_needed()
            return
        self.after(max(50, self.ai_delay_ms), self.ai_step)

    def set_chain_enabled(self, enabled: bool) -> None:
        self.chain_enabled.set(enabled)
        self.status_var.set(f"Catena {'abilitata' if enabled else 'disabilitata'}.")

    def _quick_hand_indexes(self, player_idx: int) -> list[int]:
        if self.engine is None:
            return []
        p = self.engine.state.players[player_idx]
        out: list[int] = []
        for i, uid in enumerate(p.hand):
            inst = self.engine.state.instances[uid]
            ctype = inst.definition.card_type.lower()
            is_moribondo = inst.definition.name.lower().strip() == "moribondo"
            if ctype in {"benedizione", "maledizione"} or is_moribondo:
                out.append(i)
        return out

    def _default_quick_target_for(self, player_idx: int, hand_idx: int) -> str | None:
        if self.engine is None:
            return None
        p = self.engine.state.players[player_idx]
        uid = p.hand[hand_idx]
        inst = self.engine.state.instances[uid]
        ctype = inst.definition.card_type.lower()
        if inst.definition.name.lower().strip() == "moribondo":
            for i in range(3):
                if p.attack[i] is not None:
                    return f"a{i+1}"
                if p.defense[i] is not None:
                    return f"d{i+1}"
            return None
        if ctype == "benedizione":
            for i in range(3):
                if p.attack[i] is not None:
                    return f"a{i+1}"
                if p.defense[i] is not None:
                    return f"d{i+1}"
            return None
        opp = self.engine.state.players[1 - player_idx]
        for i in range(3):
            if opp.attack[i] is not None:
                return f"a{i+1}"
            if opp.defense[i] is not None:
                return f"d{i+1}"
        for i in range(4):
            if opp.artifacts[i] is not None:
                return f"r{i+1}"
        if opp.building is not None:
            return "b"
        return None

    def _is_ai_player(self, player_idx: int) -> bool:
        return self.mode_var.get() == "ai" and player_idx == 1

    def _prompt_human_chain_decision(self, player_idx: int) -> bool:
        if self.engine is None:
            return False
        p = self.engine.state.players[player_idx]
        return messagebox.askyesno("Catena", f"{p.name}, vuoi attivare carte in catena ora?")

    def _register_chain_pass_current(self) -> None:
        if not self.chain_active or self.engine is None:
            return
        self.chain_pass_count += 1
        if self.chain_pass_count >= 2:
            self.end_chain()
            return
        self.chain_priority_idx = 1 - self.chain_priority_idx
        self.refresh()
        self._handle_chain_priority()

    def _handle_chain_priority(self) -> None:
        if not self.chain_active or self.engine is None:
            return
        prio = self.chain_priority_idx
        if self._is_ai_player(prio):
            self._maybe_ai_chain_action()
            return
        # Human side: always ask whether they want to activate now.
        wants = self._prompt_human_chain_decision(prio)
        if not wants:
            self._register_chain_pass_current()

    def start_chain(self, actor_idx: int) -> None:
        if self.engine is None or not self.chain_enabled.get() or self.chain_active:
            return
        defender_idx = 1 - actor_idx
        if not self._quick_hand_indexes(defender_idx):
            return
        self.chain_active = True
        self.chain_priority_idx = defender_idx
        self.chain_pass_count = 0
        self.refresh()
        self._handle_chain_priority()

    def _maybe_ai_chain_action(self) -> None:
        if self.engine is None or not self.chain_active:
            return
        if not self._is_ai_player(self.chain_priority_idx):
            return
        # AI either plays one quick response or passes priority.
        played = False
        for i in self._quick_hand_indexes(1):
            target = self._default_quick_target_for(1, i)
            res = self.engine.quick_play(1, i, target)
            if res.ok:
                played = True
                break
        if played:
            self.chain_pass_count = 0
            self.chain_priority_idx = 0
            self.refresh()
            self._handle_chain_priority()
            return
        self._register_chain_pass_current()

    def end_chain(self) -> None:
        self.chain_active = False
        self.chain_pass_count = 0
        # Resume AI main turn if it was paused waiting for chain resolution.
        if self.engine and self.ai_running and self.engine.state.active_player == 1:
            self.after(max(50, self.ai_delay_ms), self.ai_step)
        self.refresh()

    def chain_ok(self) -> None:
        if not self.chain_active or self.engine is None:
            return
        self._register_chain_pass_current()

    def refresh(self) -> None:
        if self.engine is None:
            return
        st = self.engine.state
        own_idx = self.current_human_idx() or 0
        enemy_idx = 1 - own_idx
        own = st.players[own_idx]
        enemy = st.players[enemy_idx]
        self.info_label.configure(
            text=(
                f"Fase: {st.phase} | Turno {st.turn_number} | Attivo: {st.players[st.active_player].name} | "
                f"{own.name} Peccato {own.sin}/100 | {enemy.name} Peccato {enemy.sin}/100"
            )
        )

        self._set_slot_widgets(self.own_attack, own.attack)
        self._set_slot_widgets(self.own_defense, own.defense)
        self._set_slot_widgets(self.own_artifacts, own.artifacts)
        self.own_building.configure(text=self.card_label(own.building))

        self._set_slot_widgets(self.enemy_attack, enemy.attack)
        self._set_slot_widgets(self.enemy_defense, enemy.defense)
        self._set_slot_widgets(self.enemy_artifacts, enemy.artifacts)
        self.enemy_building.configure(text=self.card_label(enemy.building))

        self.hand_list.delete(0, tk.END)
        for i, uid in enumerate(own.hand):
            c = st.instances[uid].definition
            cost = c.faith or 0
            self.hand_list.insert(tk.END, f"[{i}] {c.name} ({c.card_type}) costo={cost}")

        self._append_new_logs()

        if st.winner is not None:
            winner = st.players[st.winner].name
            self.status_var.set(f"Partita terminata. Vince {winner}")
        else:
            status = (
                f"{own.name}: Peccato {own.sin}/100 | {enemy.name}: Peccato {enemy.sin}/100 | "
                f"Ispirazione {own.inspiration} | Mano {len(own.hand)} | Deck {len(own.deck)}"
            )
            if self.chain_active:
                prio = st.players[self.chain_priority_idx].name
                status += f" | CATENA: priorita {prio} (OK Catena = passa)"
            self.status_var.set(status)

    def _set_slot_widgets(self, widgets, slots) -> None:
        for i, uid in enumerate(slots):
            widgets[i].configure(text=self.card_label(uid))

    def _append_new_logs(self) -> None:
        if self.engine is None:
            return
        logs = self.engine.state.logs
        if self.last_log_idx >= len(logs):
            return
        self.log_text.configure(state="normal")
        for line in logs[self.last_log_idx :]:
            self.log_text.insert(tk.END, f"{line}\n")
        self.last_log_idx = len(logs)
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def card_label(self, uid: str | None) -> str:
        if not uid or self.engine is None:
            return "-"
        inst = self.engine.state.instances[uid]
        faith = f" F:{inst.current_faith}" if inst.current_faith is not None else ""
        ctype = inst.definition.card_type.lower()
        if ctype in {"santo", "token"}:
            strength = f" P:{self.engine.get_effective_strength(uid)}"
        else:
            strength = ""
        return f"{inst.definition.name}{faith}{strength}"

    def on_hand_right_click(self, event) -> None:
        if self.engine is None or not self.can_human_act():
            return
        idx = self.hand_list.nearest(event.y)
        if idx < 0:
            return
        own_idx = self.current_human_idx() or 0
        hand = self.engine.state.players[own_idx].hand
        if idx >= len(hand):
            return
        uid = hand[idx]
        inst = self.engine.state.instances[uid]
        ctype = inst.definition.card_type.lower()
        is_moribondo = inst.definition.name.lower().strip() == "moribondo"

        menu = tk.Menu(self, tearoff=0)
        if self.chain_active and (ctype in {"benedizione", "maledizione"} or is_moribondo):
            if self._card_requires_target(uid):
                menu.add_command(label="Gioca Effetto...", command=lambda uu=uid: self.ask_guided_quick_target(uu))
            else:
                menu.add_command(label="Gioca Effetto", command=lambda uu=uid: self.play_uid(uu, None))
        elif ctype in {"santo", "token"}:
            m_att = tk.Menu(menu, tearoff=0)
            for s in range(1, 4):
                m_att.add_command(label=f"Attacco {s}", command=lambda uu=uid, ss=s: self.play_uid(uu, f"a{ss}"))
            menu.add_cascade(label="Gioca in Attacco", menu=m_att)
            m_def = tk.Menu(menu, tearoff=0)
            for s in range(1, 4):
                m_def.add_command(label=f"Difesa {s}", command=lambda uu=uid, ss=s: self.play_uid(uu, f"d{ss}"))
            menu.add_cascade(label="Gioca in Difesa", menu=m_def)
        elif ctype in {"benedizione", "maledizione"}:
            if self._card_requires_target(uid):
                menu.add_command(label="Gioca Effetto...", command=lambda uu=uid: self.ask_guided_quick_target(uu))
            else:
                menu.add_command(label="Gioca Effetto", command=lambda uu=uid: self.play_uid(uu, None))
        else:
            menu.add_command(label="Gioca", command=lambda uu=uid: self.play_uid(uu, None))

        menu.tk_popup(event.x_root, event.y_root)

    def on_hand_select(self, _event) -> None:
        if self.engine is None:
            return
        own_idx = self.current_human_idx() or 0
        sel = self.hand_list.curselection()
        if not sel:
            return
        idx = sel[0]
        hand = self.engine.state.players[own_idx].hand
        if idx < 0 or idx >= len(hand):
            return
        self.show_card_detail(hand[idx])

    def show_board_card_detail(self, relative_player: int, zone: str, idx: int) -> None:
        if self.engine is None:
            return
        human_idx = self.current_human_idx() or 0
        player_idx = human_idx if relative_player == 0 else 1 - human_idx
        player = self.engine.state.players[player_idx]
        uid: str | None = None
        if zone == "attack":
            uid = player.attack[idx]
        elif zone == "defense":
            uid = player.defense[idx]
        elif zone == "artifacts":
            uid = player.artifacts[idx]
        elif zone == "building":
            uid = player.building
        if uid:
            self.show_card_detail(uid)

    def show_card_detail(self, uid: str) -> None:
        if self.engine is None:
            return
        inst = self.engine.state.instances[uid]
        c = inst.definition
        effect = (c.effect_text or "").strip() or "Nessun effetto testuale disponibile."
        detail = effect
        self.card_detail_text.configure(state="normal")
        self.card_detail_text.delete("1.0", tk.END)
        self.card_detail_text.insert(tk.END, detail)
        self.card_detail_text.configure(state="disabled")

    def _card_allows_multi_target(self, uid: str) -> bool:
        if self.engine is None:
            return False
        txt = (self.engine.state.instances[uid].definition.effect_text or "").lower()
        return (
            "scegli due" in txt
            or "due santi" in txt
            or "2 carte" in txt
            or "due carte" in txt
            or "2 bersagli" in txt
            or "due bersagli" in txt
            or "fino a 2" in txt
            or "fino a due" in txt
            or "scegli 3" in txt
            or "3 bersagli" in txt
            or "scegli 5" in txt
            or "5 bersagli" in txt
            or ("santo" in txt and ("artefatto" in txt or "edificio" in txt))
        )

    def _card_requires_target(self, uid: str) -> bool:
        if self.engine is None:
            return False
        txt = (self.engine.state.instances[uid].definition.effect_text or "").lower().strip()
        if not txt:
            return False
        target_markers = [
            "scegli",
            "bersaglio",
            "equipaggia",
            "su un tuo santo",
            "su un santo",
            "santo avversario",
            "tuo santo",
            "cerca nel reliquiario",
            "cerca nel cimitero",
            "carta scomunicata",
            "dal cimitero",
            "dal reliquiario",
            "distruggi un santo",
            "distruggi due santi",
            "artefatto avversario",
            "edificio avversario",
        ]
        return any(m in txt for m in target_markers)

    def _target_selection_limits(self, uid: str) -> tuple[int, int | None]:
        if self.engine is None:
            return (0, None)
        txt = (self.engine.state.instances[uid].definition.effect_text or "").lower()

        # Most common explicit counts.
        if any(k in txt for k in ["scegli 5", "5 bersagli"]):
            return (5, 5)
        if any(k in txt for k in ["scegli 3", "3 bersagli"]):
            return (3, 3)
        if any(k in txt for k in ["scegli due", "due santi", "2 carte", "due carte", "2 bersagli", "due bersagli"]):
            return (2, 2)
        if any(k in txt for k in ["fino a 2", "fino a due"]):
            return (0, 2)
        # Effects that normally require two different targets.
        if "santo" in txt and ("artefatto" in txt or "edificio" in txt):
            return (2, 2)
        # Default: optional single target.
        return (0, 1)

    def _norm_text(self, text: str) -> str:
        return text.lower().strip()

    def _guided_target_candidates(self, uid: str) -> list[str]:
        if self.engine is None:
            return []
        engine = self.engine
        own_idx = self.current_human_idx() or 0
        opp_idx = 1 - own_idx
        own = engine.state.players[own_idx]
        opp = engine.state.players[opp_idx]
        inst = engine.state.instances[uid]
        txt = self._norm_text(inst.definition.effect_text or "")
        ctype = inst.definition.card_type.lower().strip()
        out: list[str] = []

        wants_deck = "reliquiario" in txt and ("cerca" in txt or "aggiung" in txt)
        wants_grave = "cimitero" in txt
        wants_excom = "scomunicat" in txt
        wants_opp_art = "artefatto" in txt and "avversar" in txt
        wants_opp_building = "edificio" in txt and "avversar" in txt
        wants_opp_saints = (
            "santo avversario" in txt
            or ("avversar" in txt and "santo" in txt)
            or (ctype == "maledizione" and "tuo santo" not in txt and "sul tuo terreno" not in txt)
        )
        wants_own_saints = "tuo santo" in txt or "sul tuo terreno" in txt or "tuoi santi" in txt

        # No signal from effect text: no guided candidates.
        if not any([wants_deck, wants_grave, wants_excom, wants_opp_art, wants_opp_building, wants_opp_saints, wants_own_saints]):
            return []

        if wants_own_saints:
            for i in range(3):
                if own.attack[i] is not None:
                    out.append(f"a{i+1}")
                if own.defense[i] is not None:
                    out.append(f"d{i+1}")

        if wants_opp_saints:
            for i in range(3):
                if opp.attack[i] is not None:
                    out.append(f"a{i+1}")
                if opp.defense[i] is not None:
                    out.append(f"d{i+1}")

        if wants_opp_art:
            for i in range(4):
                if opp.artifacts[i] is not None:
                    out.append(f"r{i+1}")
        if wants_opp_building and opp.building is not None:
            out.append("b")

        def _filter_name(card_uid: str) -> bool:
            name = self._norm_text(engine.state.instances[card_uid].definition.name)
            ctype_name = self._norm_text(engine.state.instances[card_uid].definition.card_type)
            if "\"giorno\"" in txt or " carte \"giorno\"" in txt or "carte giorno" in txt:
                return "giorno" in name
            if "artefatto" in txt and "reliquiario" in txt:
                return ctype_name == "artefatto"
            if "benedizione o maledizione" in txt or "benedizione/maledizione" in txt:
                return ctype_name in {"benedizione", "maledizione"}
            if "santo" in txt and "reliquiario" in txt:
                return ctype_name in {"santo", "token"}
            return True

        if wants_deck:
            for c_uid in own.deck:
                if _filter_name(c_uid):
                    out.append(f"deck:{engine.state.instances[c_uid].definition.name}")
        if wants_grave:
            for c_uid in own.graveyard:
                if _filter_name(c_uid):
                    out.append(f"grave:{engine.state.instances[c_uid].definition.name}")
        if wants_excom:
            for c_uid in own.excommunicated:
                if _filter_name(c_uid):
                    out.append(f"excom:{engine.state.instances[c_uid].definition.name}")
        return list(dict.fromkeys(out))

    def _format_guided_candidate(self, token: str, own_idx: int) -> str:
        if self.engine is None:
            return token
        st = self.engine.state
        own = st.players[own_idx]
        opp = st.players[1 - own_idx]
        if token.startswith("a") and len(token) == 2 and token[1].isdigit():
            i = int(token[1]) - 1
            own_uid = own.attack[i] if 0 <= i < 3 else None
            opp_uid = opp.attack[i] if 0 <= i < 3 else None
            own_name = st.instances[own_uid].definition.name if own_uid is not None else "-"
            opp_name = st.instances[opp_uid].definition.name if opp_uid is not None else "-"
            return f"Slot Attacco {i + 1} | Tuo: {own_name} | Avv: {opp_name}"
        if token.startswith("d") and len(token) == 2 and token[1].isdigit():
            i = int(token[1]) - 1
            own_uid = own.defense[i] if 0 <= i < 3 else None
            opp_uid = opp.defense[i] if 0 <= i < 3 else None
            own_name = st.instances[own_uid].definition.name if own_uid is not None else "-"
            opp_name = st.instances[opp_uid].definition.name if opp_uid is not None else "-"
            return f"Slot Difesa {i + 1} | Tuo: {own_name} | Avv: {opp_name}"
        if token.startswith("r") and len(token) == 2 and token[1].isdigit():
            i = int(token[1]) - 1
            opp_uid = opp.artifacts[i] if 0 <= i < 4 else None
            opp_name = st.instances[opp_uid].definition.name if opp_uid is not None else "-"
            return f"Artefatto Avversario {i + 1} | {opp_name}"
        if token == "b":
            opp_name = st.instances[opp.building].definition.name if opp.building else "-"
            return f"Edificio Avversario | {opp_name}"
        if ":" in token:
            pref, name = token.split(":", 1)
            if pref == "deck":
                return f"Reliquiario | {name}"
            if pref == "grave":
                return f"Cimitero | {name}"
            if pref == "excom":
                return f"Scomunicate | {name}"
            return f"{pref} | {name}"
        return token

    def _open_target_picker(
        self,
        *,
        title: str,
        prompt: str,
        choices: list[tuple[str, str]],
        allow_multi: bool,
        min_targets: int = 0,
        max_targets: int | None = None,
        allow_none: bool = True,
        allow_manual: bool = False,
    ) -> tuple[bool, str | None]:
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry("620x540")
        ttk.Label(win, text=prompt).pack(anchor="w", padx=8, pady=6)
        if allow_multi:
            lim = ""
            if min_targets > 0 and max_targets is not None and min_targets == max_targets:
                lim = f" (seleziona esattamente {min_targets})"
            elif max_targets is not None:
                lim = f" (min {min_targets}, max {max_targets})"
            ttk.Label(win, text=f"Selezione multipla: clicca tutti i bersagli necessari{lim}.").pack(anchor="w", padx=8)
        lb = tk.Listbox(win, selectmode=("multiple" if allow_multi else "browse"))
        lb.pack(fill="both", expand=True, padx=8, pady=6)
        for label, _token in choices:
            lb.insert(tk.END, label)
        selected: dict[str, str | None] = {"value": ""}

        manual_var = tk.StringVar(value="")
        if allow_manual:
            row = ttk.Frame(win)
            row.pack(fill="x", padx=8, pady=(0, 4))
            ttk.Label(row, text="Valore manuale (opzionale):").pack(side="left")
            ttk.Entry(row, textvariable=manual_var).pack(side="left", fill="x", expand=True, padx=6)

        def _ok() -> None:
            raw_manual = manual_var.get().strip() if allow_manual else ""
            if raw_manual:
                selected["value"] = raw_manual
                win.destroy()
                return
            idxs = list(lb.curselection())
            chosen_count = len(idxs)
            upper = max_targets if max_targets is not None else (9999 if allow_multi else 1)
            if chosen_count < min_targets or chosen_count > upper:
                if max_targets is not None and min_targets == max_targets:
                    messagebox.showwarning("Selezione non valida", f"Devi selezionare esattamente {min_targets} bersagli.")
                elif max_targets is not None:
                    messagebox.showwarning("Selezione non valida", f"Seleziona tra {min_targets} e {max_targets} bersagli.")
                else:
                    messagebox.showwarning("Selezione non valida", f"Seleziona almeno {min_targets} bersagli.")
                return
            if not idxs:
                selected["value"] = None if allow_none else ""
            else:
                selected["value"] = ",".join(choices[i][1] for i in idxs)
            win.destroy()

        def _no_target() -> None:
            selected["value"] = None
            win.destroy()

        def _cancel() -> None:
            selected["value"] = ""
            win.destroy()

        btn = ttk.Frame(win)
        btn.pack(fill="x", padx=8, pady=8)
        ttk.Button(btn, text="OK", command=_ok).pack(side="left")
        if allow_none:
            ttk.Button(btn, text="Senza Target", command=_no_target).pack(side="left", padx=6)
        ttk.Button(btn, text="Annulla", command=_cancel).pack(side="left", padx=6)
        win.transient(self)
        win.grab_set()
        self.wait_window(win)
        return (selected["value"] == "", selected["value"])

    def ask_guided_quick_target(self, uid: str) -> None:
        if not self._card_requires_target(uid):
            self.play_uid(uid, None)
            return
        candidates = self._guided_target_candidates(uid)
        multi = self._card_allows_multi_target(uid)
        min_targets, max_targets = self._target_selection_limits(uid)
        own_idx = self.current_human_idx() or 0
        choices = [(self._format_guided_candidate(c, own_idx), c) for c in candidates]
        if not choices:
            messagebox.showwarning("Selezione Bersaglio", "Nessun bersaglio valido disponibile per questa carta.")
            return
        canceled, selected = self._open_target_picker(
            title="Selezione Bersaglio",
            prompt="Seleziona i bersagli validi dalla lista.",
            choices=choices,
            allow_multi=multi,
            min_targets=min_targets,
            max_targets=max_targets,
            allow_none=True,
            allow_manual=True,
        )
        if canceled:
            return
        self.play_uid(uid, selected)

    def play_uid(self, uid: str, target: str | None) -> None:
        if self.engine is None or not self.can_human_act():
            return
        own_idx = self.current_human_idx() or 0
        hand = self.engine.state.players[own_idx].hand
        if uid not in hand:
            return
        idx = hand.index(uid)
        if self.chain_active:
            ctype = self.engine.state.instances[uid].definition.card_type.lower()
            is_moribondo = self.engine.state.instances[uid].definition.name.lower().strip() == "moribondo"
            if ctype not in {"benedizione", "maledizione"} and not is_moribondo:
                messagebox.showwarning("Catena", "Durante la catena puoi giocare solo Benedizioni/Maledizioni.")
                return
            res = self.engine.quick_play(own_idx, idx, target)
            if res.ok:
                self.chain_pass_count = 0
                self.chain_priority_idx = 1 - own_idx
                self.refresh()
                self._handle_chain_priority()
        else:
            res = self.engine.play_card(own_idx, idx, target)
            if res.ok:
                self.start_chain(actor_idx=own_idx)
        if not res.ok:
            messagebox.showwarning("Azione non valida", res.message)
        self.refresh()
        if not self.chain_active:
            self.begin_turn_if_needed()

    def on_own_slot_right_click(self, source: str) -> None:
        if self.engine is None or not self.can_human_act():
            return
        own_idx = self.current_human_idx() or 0
        uid = self.engine.resolve_board_uid(own_idx, source)
        if uid is None:
            return
        menu = tk.Menu(self, tearoff=0)
        if source.startswith("a"):
            slot = int(source[1])
            m_attack = tk.Menu(menu, tearoff=0)
            m_attack.add_command(label="Attacco diretto", command=lambda s=slot: self.do_attack(s - 1, None))
            for t in range(1, 4):
                m_attack.add_command(label=f"Target t{t}", command=lambda s=slot, tt=t: self.do_attack(s - 1, tt - 1))
            menu.add_cascade(label="Attacca", menu=m_attack)
        menu.add_command(label="Attiva abilita", command=lambda src=source: self.do_activate(src))
        menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())

    def do_attack(self, from_slot: int, target_slot: int | None) -> None:
        if self.engine is None or not self.can_human_act():
            return
        if self.chain_active:
            messagebox.showwarning("Catena", "Durante la catena puoi solo giocare carte rapide o passare con OK Catena.")
            return
        own_idx = self.current_human_idx() or 0
        res = self.engine.attack(own_idx, from_slot, target_slot)
        if res.ok:
            self.start_chain(actor_idx=own_idx)
        if not res.ok:
            messagebox.showwarning("Attacco non valido", res.message)
        self.refresh()
        self.begin_turn_if_needed()

    def do_activate(self, source: str) -> None:
        if self.engine is None or not self.can_human_act():
            return
        if self.chain_active:
            messagebox.showwarning("Catena", "Durante la catena puoi solo giocare carte rapide o passare con OK Catena.")
            return
        own_idx = self.current_human_idx() or 0
        uid = self.engine.resolve_board_uid(own_idx, source)
        choices: list[tuple[str, str]] = []
        min_targets = 0
        max_targets: int | None = 1
        if uid:
            choices = [(self._format_guided_candidate(c, own_idx), c) for c in self._guided_target_candidates(uid)]
            min_targets, max_targets = self._target_selection_limits(uid)
        canceled, target = self._open_target_picker(
            title="Attiva Abilita",
            prompt="Seleziona un bersaglio per l'abilita, oppure inserisci un valore manuale.",
            choices=choices,
            allow_multi=(max_targets is None or max_targets > 1),
            min_targets=min_targets,
            max_targets=max_targets,
            allow_none=True,
            allow_manual=True,
        )
        if canceled:
            return
        res = self.engine.activate_ability(own_idx, source, target)
        if res.ok:
            self.start_chain(actor_idx=own_idx)
        if not res.ok:
            messagebox.showwarning("Abilita non valida", res.message)
        self.refresh()
        self.begin_turn_if_needed()

    def end_turn(self) -> None:
        if self.engine is None or self.ai_running:
            return
        if self.chain_active:
            messagebox.showwarning("Catena", "Chiudi prima la catena (OK Catena fino a doppio pass).")
            return
        if not self.can_human_act():
            return
        self.engine.end_turn()
        self.turn_started = False
        self.refresh()
        self.begin_turn_if_needed()

    def save_game(self) -> None:
        if self.engine is None:
            return
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        self.engine.state.save(path)
        self.status_var.set(f"Partita salvata: {path}")

    def export_log(self) -> None:
        if self.engine is None:
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt")])
        if not path:
            return
        self.engine.export_logs(path)
        self.status_var.set(f"Log esportato: {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Holy War - GUI MVP")
    parser.add_argument("--deck-xlsx", type=str, default=None, help="Percorso a Holy War.xlsx")
    parser.add_argument("--cards-json", type=str, default="holywar/data/cards.json", help="Cache JSON carte")
    parser.add_argument("--premades-json", type=str, default=None, help="Importa deck premade custom da JSON")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--ai-delay", type=float, default=1.0)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.premades_json:
        register_premades_from_json(args.premades_json)
    cards = ensure_cards(args)
    app = HolyWarGUI(cards, seed=args.seed, ai_delay=args.ai_delay)
    app.mainloop()


if __name__ == "__main__":
    main()
