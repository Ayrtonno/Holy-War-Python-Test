from __future__ import annotations

import json
import tkinter as tk
from tkinter import messagebox, ttk

from holywar.effects.runtime import runtime_cards


class GUIGameViewMixin:
    """Board/hand rendering and user interaction handlers."""

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

    def _build_resource_panel(self, parent, caption: str) -> None:
        panel = ttk.Frame(parent)
        panel.pack(side="left", fill="x", expand=True, padx=4, pady=4)
        name = ttk.Label(panel, text=f"{caption}: -")
        name.grid(row=0, column=0, sticky="w")
        ttk.Label(panel, text="Peccato").grid(row=1, column=0, sticky="w", pady=(2, 0))
        sin_lbl = ttk.Label(panel, text="0/100")
        sin_lbl.grid(row=1, column=1, sticky="w", padx=6, pady=(2, 0))
        sin_bar = ttk.Progressbar(panel, mode="determinate", maximum=100, length=170)
        sin_bar.grid(row=1, column=2, sticky="ew", padx=(0, 6), pady=(2, 0))
        ttk.Label(panel, text="Ispirazione").grid(row=2, column=0, sticky="w")
        insp_lbl = ttk.Label(panel, text="0")
        insp_lbl.grid(row=2, column=1, sticky="w", padx=6)
        hand_lbl = ttk.Label(panel, text="Mano 0")
        hand_lbl.grid(row=2, column=2, sticky="e")
        deck_lbl = ttk.Label(panel, text="Deck 0")
        deck_lbl.grid(row=3, column=2, sticky="e")
        panel.columnconfigure(2, weight=1)
        self.resource_name_labels.append(name)
        self.resource_sin_labels.append(sin_lbl)
        self.resource_insp_labels.append(insp_lbl)
        self.resource_hand_labels.append(hand_lbl)
        self.resource_deck_labels.append(deck_lbl)
        self.resource_sin_bars.append(sin_bar)

    def refresh(self) -> None:
        if self.engine is None:
            return
        # Any real state refresh invalidates the cached preview snapshot.
        self._sim_state_snapshot = None
        self._clear_slot_highlights()
        st = self.engine.state
        own_idx = self.current_human_idx() or 0
        enemy_idx = 1 - own_idx
        own = st.players[own_idx]
        enemy = st.players[enemy_idx]
        self.info_label.configure(
            text=(
                f"Fase: {st.phase.upper()} | Turno {st.turn_number} | Attivo: {st.players[st.active_player].name}"
            )
        )
        self._update_resource_panel(0, own)
        self._update_resource_panel(1, enemy)

        self._set_slot_widgets(self.own_attack, own.attack)
        self._set_slot_widgets(self.own_defense, own.defense)
        self._set_slot_widgets(self.own_artifacts, own.artifacts, hide_equipped=True)
        self.own_building.configure(text=self.card_label(own.building))

        self._set_slot_widgets(self.enemy_attack, enemy.attack)
        self._set_slot_widgets(self.enemy_defense, enemy.defense)
        self._set_slot_widgets(self.enemy_artifacts, enemy.artifacts, hide_equipped=True)
        self.enemy_building.configure(text=self.card_label(enemy.building))

        self.hand_list.delete(0, tk.END)
        for i, uid in enumerate(own.hand):
            self.hand_list.insert(tk.END, self.hand_entry_label(i, uid))

        self._append_new_logs()

        if st.winner is not None:
            winner = st.players[st.winner].name
            self.status_var.set(f"Partita terminata. Vince {winner}")
        else:
            status = (
                f"{own.name}: Peccato {own.sin}/100 | Ispirazione {int(own.inspiration) + int(getattr(own, 'temporary_inspiration', 0))} | Mano {len(own.hand)} | Deck {len(own.deck)}"
            )
            if self.chain_active:
                prio = st.players[self.chain_priority_idx].name
                status += f" | CATENA: priorita {prio} (OK Catena = passa)"
            self.status_var.set(status)
        self.after_idle(self._maybe_show_runtime_reveal)

    def _maybe_show_runtime_reveal(self) -> None:
        if self.engine is None or self._reveal_prompt_open:
            return

        flags = self.engine.state.flags
        waiting = bool(flags.get("_runtime_waiting_for_reveal"))
        reveal_uid = str(flags.get("_runtime_reveal_card", "")).strip()

        if not waiting or not reveal_uid:
            self._reveal_prompt_last_uid = ""
            return

        if reveal_uid == self._reveal_prompt_last_uid:
            return

        inst = self.engine.state.instances.get(reveal_uid)
        if inst is None:
            flags["_runtime_waiting_for_reveal"] = False
            flags.pop("_runtime_reveal_card", None)
            self._reveal_prompt_last_uid = ""
            return

        self._reveal_prompt_open = True
        self._reveal_prompt_last_uid = reveal_uid
        try:
            choice_candidates_raw = str(flags.get("_runtime_choice_candidates", "")).strip()
            choice_values_raw = str(flags.get("_runtime_choice_values", "")).strip()

            if choice_candidates_raw:
                candidate_uids = [v for v in choice_candidates_raw.split(";;") if v]
                choice_owner = int(str(flags.get("_runtime_choice_owner", "0")) or "0")
                choices: list[tuple[str, str]] = []
                for c_uid in candidate_uids:
                    c_inst = self.engine.state.instances.get(c_uid)
                    if c_inst is None:
                        continue
                    choices.append((self._format_guided_candidate(c_uid, choice_owner), c_uid))

                title = str(flags.get("_runtime_choice_title", "Scegli Carta")) or "Scegli Carta"
                prompt = (
                    str(flags.get("_runtime_choice_prompt", "")).strip()
                    or "Scegli una carta tra le prime del reliquiario oppure Nessuna."
                )
                min_targets = int(str(flags.get("_runtime_choice_min_targets", "0")) or "0")
                max_targets_raw = str(flags.get("_runtime_choice_max_targets", "1")).strip()
                max_targets = int(max_targets_raw) if max_targets_raw else 1
                allow_multi = max_targets != 1

                canceled, selected = self._open_board_target_picker(
                    title=title,
                    prompt=prompt,
                    choices=choices,
                    allow_multi=allow_multi,
                    min_targets=min_targets,
                    max_targets=max_targets,
                    allow_none=True,
                    allow_manual=False,
                    card_uid=reveal_uid,
                )
                flags["_runtime_choice_selected"] = "" if canceled or not selected else str(selected)
                flags["_runtime_choice_ready"] = True

            elif choice_values_raw:
                values = [v for v in choice_values_raw.split(";;") if v]
                labels_raw = str(flags.get("_runtime_choice_labels", "")).strip()
                try:
                    labels_map = json.loads(labels_raw) if labels_raw else {}
                except Exception:
                    labels_map = {}

                choices: list[tuple[str, str]] = []
                for value in values:
                    label = str(labels_map.get(value, value))
                    choices.append((label, value))

                title = str(flags.get("_runtime_choice_title", "Scegli un'opzione")) or "Scegli un'opzione"
                prompt = str(flags.get("_runtime_choice_prompt", "")).strip() or "Seleziona una modalità."
                min_targets = int(str(flags.get("_runtime_choice_min_targets", "1")) or "1")
                max_targets_raw = str(flags.get("_runtime_choice_max_targets", "1")).strip()
                max_targets = int(max_targets_raw) if max_targets_raw else 1
                allow_multi = max_targets != 1

                canceled, selected = self._open_board_target_picker(
                    title=title,
                    prompt=prompt,
                    choices=choices,
                    allow_multi=allow_multi,
                    min_targets=min_targets,
                    max_targets=max_targets,
                    allow_none=False,
                    allow_manual=False,
                    card_uid=reveal_uid,
                )
                flags["_runtime_choice_selected"] = "" if canceled or not selected else str(selected)
                flags["_runtime_choice_ready"] = True

            else:
                messagebox.showinfo(
                    "Carta rivelata",
                    f"Hai rivelato: {inst.definition.name}\n\nPremi OK per continuare la risoluzione dell'effetto.",
                )
        finally:
            self._reveal_prompt_open = False

        flags["_runtime_waiting_for_reveal"] = False
        flags.pop("_runtime_reveal_card", None)
        runtime_cards.resume_pending_effect(self.engine)

        pending_actor = self._post_reveal_chain_actor
        self._post_reveal_chain_actor = None
        self._reveal_prompt_last_uid = ""

        self.refresh()
        if pending_actor is not None:
            self.start_chain(actor_idx=pending_actor)

    def _update_resource_panel(self, panel_idx: int, player) -> None:
        if panel_idx >= len(self.resource_name_labels):
            return
        self.resource_name_labels[panel_idx].configure(text=player.name)
        self.resource_sin_labels[panel_idx].configure(text=f"{player.sin}/100")
        total_inspiration = int(player.inspiration) + int(getattr(player, "temporary_inspiration", 0))
        self.resource_insp_labels[panel_idx].configure(text=str(total_inspiration))
        self.resource_hand_labels[panel_idx].configure(text=f"Mano {len(player.hand)}")
        self.resource_deck_labels[panel_idx].configure(text=f"Deck {len(player.deck)}")
        self.resource_sin_bars[panel_idx]["value"] = max(0, min(100, player.sin))

    def hand_entry_label(self, hand_idx: int, uid: str) -> str:
        if self.engine is None:
            return "-"
        inst = self.engine.state.instances[uid]
        c = inst.definition
        faith = inst.current_faith if inst.current_faith is not None else c.faith
        f_txt = f"F:{faith}" if faith is not None else "F:-"
        p_txt = ""
        if c.card_type.lower().strip() in {"santo", "token"}:
            p_txt = f" | P:{self.engine.get_effective_strength(uid)}"
        return f"[{hand_idx}] {c.name} ({c.card_type}) | {f_txt}{p_txt}"

    def _set_slot_widgets(self, widgets, slots, *, hide_equipped: bool = False) -> None:
        for i, uid in enumerate(slots):
            widget = widgets[i]
            display_uid = uid
            if hide_equipped and self._is_equipment_card_equipped(uid):
                display_uid = None
            widget.configure(text=self.card_label(display_uid))
            self._apply_equipment_highlight(widget, display_uid)

    def _equipped_uids_for(self, uid: str | None) -> list[str]:
        if self.engine is None or not uid:
            return []
        inst = self.engine.state.instances.get(uid)
        if inst is None:
            return []
        out: list[str] = []
        for tag in list(inst.blessed):
            if not isinstance(tag, str) or not tag.startswith("equipped_by:"):
                continue
            eq_uid = tag.split(":", 1)[1].strip()
            if not eq_uid or eq_uid not in self.engine.state.instances:
                continue
            if eq_uid not in out:
                out.append(eq_uid)
        return out

    def _is_equipment_card_equipped(self, uid: str | None) -> bool:
        if self.engine is None or not uid:
            return False
        inst = self.engine.state.instances.get(uid)
        if inst is None:
            return False
        for tag in list(inst.blessed):
            if isinstance(tag, str) and tag.startswith("equipped_to:"):
                return True
        return False

    def _apply_equipment_highlight(self, widget, uid: str | None) -> None:
        has_equipment = bool(self._equipped_uids_for(uid))
        color = "red" if has_equipment else "black"
        # tk.Button uses "fg", ttk widgets generally use "foreground".
        try:
            widget.configure(fg=color)
        except tk.TclError:
            try:
                widget.configure(foreground=color)
            except tk.TclError:
                pass

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
        self._clear_slot_highlights()
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
        if self._is_monsone_card(uid):
            menu.add_command(label="Gioca Effetto...", command=lambda uu=uid: self.ask_guided_quick_target(uu))
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
            return
        if self.chain_active and (ctype in {"benedizione", "maledizione"} or is_moribondo):
            valid_targets = self._valid_play_targets(own_idx, idx, uid, quick=True)
            if valid_targets:
                self._set_slot_highlights(valid_targets, card_uid=uid)
                menu.add_command(label="Gioca Effetto...", command=lambda uu=uid: self.ask_guided_quick_target(uu))
            elif self._can_play_target(own_idx, idx, None, quick=True):
                menu.add_command(label="Gioca Effetto", command=lambda uu=uid: self.play_uid(uu, None))
            else:
                menu.add_command(label="Nessun target valido", state="disabled")
        elif ctype in {"santo", "token"}:
            play_owner = self._play_owner_idx(uid)
            m_att = tk.Menu(menu, tearoff=0)
            att_targets: list[str] = []
            for s in range(1, 4):
                target = f"a{s}"
                if self._can_play_target(own_idx, idx, target):
                    att_targets.append(target)
                    m_att.add_command(label=f"Attacco {s}", command=lambda uu=uid, ss=s: self.play_uid(uu, f"a{ss}"))
            if not att_targets:
                m_att.add_command(label="Nessuno slot valido", state="disabled")
            menu.add_cascade(label="Gioca in Attacco", menu=m_att)
            m_def = tk.Menu(menu, tearoff=0)
            def_targets: list[str] = []
            for s in range(1, 4):
                target = f"d{s}"
                if self._can_play_target(own_idx, idx, target):
                    def_targets.append(target)
                    m_def.add_command(label=f"Difesa {s}", command=lambda uu=uid, ss=s: self.play_uid(uu, f"d{ss}"))
            if not def_targets:
                m_def.add_command(label="Nessuno slot valido", state="disabled")
            menu.add_cascade(label="Gioca in Difesa", menu=m_def)
            self._set_slot_highlights(att_targets + def_targets, side_hint="enemy" if play_owner != own_idx else "own")
        elif ctype in {"benedizione", "maledizione"}:
            valid_targets = self._valid_play_targets(own_idx, idx, uid, quick=False)
            if valid_targets:
                self._set_slot_highlights(valid_targets, card_uid=uid)
                menu.add_command(label="Gioca Effetto...", command=lambda uu=uid: self.ask_guided_quick_target(uu))
            elif self._can_play_target(own_idx, idx, None, quick=False):
                menu.add_command(label="Gioca Effetto", command=lambda uu=uid: self.play_uid(uu, None))
            else:
                menu.add_command(label="Nessun target valido", state="disabled")
        else:
            menu.add_command(label="Gioca", command=lambda uu=uid: self.play_uid(uu, None))

        menu.bind("<Unmap>", lambda _e: self._clear_slot_highlights())
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

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
        self.show_card_detail(hand[idx], effect_only=True)

    def _selected_hand_uid(self) -> str | None:
        if self.engine is None:
            return None
        own_idx = self.current_human_idx() or 0
        sel = self.hand_list.curselection()
        if not sel:
            return None
        idx = sel[0]
        hand = self.engine.state.players[own_idx].hand
        if idx < 0 or idx >= len(hand):
            return None
        return hand[idx]

    def _first_open_slot(self, player_idx: int, lane: str) -> str | None:
        if self.engine is None:
            return None
        player = self.engine.state.players[player_idx]
        slots = player.attack if lane == "a" else player.defense
        for i, uid in enumerate(slots):
            if uid is None:
                return f"{lane}{i + 1}"
        return None

    def play_selected_card(self) -> None:
        if self.engine is None or not self.can_human_act():
            return
        uid = self._selected_hand_uid()
        if uid is None:
            messagebox.showinfo("Gioca Carta", "Seleziona prima una carta dalla mano.")
            return
        own_idx = self.current_human_idx() or 0
        inst = self.engine.state.instances[uid]
        ctype = inst.definition.card_type.lower().strip()
        target: str | None = None
        if self._card_requires_target(uid):
            self.ask_guided_quick_target(uid)
            return
        if ctype in {"santo", "token"}:
            play_owner = self._play_owner_idx(uid)
            target = self._first_open_slot(play_owner, "a") or self._first_open_slot(play_owner, "d")
            if target is None:
                messagebox.showwarning("Campo pieno", "Nessuno slot libero in Attacco/Difesa.")
                return
        self.play_uid(uid, target)

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

    def show_card_detail(self, uid: str, effect_only: bool = False) -> None:
        if self.engine is None:
            return
        inst = self.engine.state.instances[uid]
        c = inst.definition
        effect = (c.effect_text or "").strip() or "Nessun effetto testuale disponibile."
        equipped_uids = self._equipped_uids_for(uid)
        equipped_section = ""
        if equipped_uids:
            lines = []
            for eq_uid in equipped_uids:
                eq_inst = self.engine.state.instances.get(eq_uid)
                if eq_inst is None:
                    continue
                eq_effect = (eq_inst.definition.effect_text or "").strip() or "Nessun effetto testuale disponibile."
                lines.append(f"- {eq_inst.definition.name}: {eq_effect}")
            if lines:
                equipped_section = "\n\nCarte equipaggiate:\n" + "\n".join(lines)
        detail = effect if effect_only else f"{c.name}\n\n{effect}{equipped_section}"
        self.card_detail_text.configure(state="normal")
        self.card_detail_text.delete("1.0", tk.END)
        self.card_detail_text.insert(tk.END, detail)
        self.card_detail_text.configure(state="disabled")

    def open_debug_zone(self, zone: str) -> None:
        engine = self.engine
        if engine is None:
            messagebox.showinfo("Debug Zone", "Avvia prima una partita.")
            return
        zone_key = str(zone).strip().lower()
        labels = {
            "deck": "Deck",
            "graveyard": "Cimitero",
            "excommunicated": "Scomunicate",
        }
        if zone_key not in labels:
            return
        player_idx = self.current_human_idx()
        if player_idx is None:
            player_idx = 0
        player = engine.state.players[player_idx]
        if zone_key == "deck":
            uids = list(player.deck)
        elif zone_key == "graveyard":
            uids = list(player.graveyard)
        else:
            uids = list(player.excommunicated)

        win = tk.Toplevel(self)
        win.title(f"{labels[zone_key]} (Debug)")
        self._center_toplevel(win, 560, 500)
        win.transient(self)

        ttk.Label(
            win,
            text=f"{labels[zone_key]} di {player.name} - {len(uids)} carte",
        ).pack(anchor="w", padx=8, pady=(8, 4))

        body = ttk.Frame(win)
        body.pack(fill="both", expand=True, padx=8, pady=8)
        lb = tk.Listbox(body)
        lb.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(body, command=lb.yview)
        lb.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")

        details = tk.Text(win, wrap="word", height=8)
        details.pack(fill="x", padx=8, pady=(0, 8))
        details.configure(state="disabled")

        for i, uid in enumerate(uids, start=1):
            inst = engine.state.instances.get(uid)
            if inst is None:
                lb.insert(tk.END, f"{i:02d}. <missing> [{uid}]")
                continue
            lb.insert(tk.END, f"{i:02d}. {inst.definition.name} [{uid}]")

        def _on_pick(_event=None):
            sel = lb.curselection()
            if not sel:
                return
            row = int(sel[0])
            if row < 0 or row >= len(uids):
                return
            uid = uids[row]
            inst = engine.state.instances.get(uid)
            if inst is None:
                text = f"{uid}\n\nCarta non trovata nelle istanze."
            else:
                cdef = inst.definition
                effect = (cdef.effect_text or "").strip() or "Nessun effetto testuale disponibile."
                text = f"{cdef.name}\nTipo: {cdef.card_type}\nUID: {uid}\n\n{effect}"
            details.configure(state="normal")
            details.delete("1.0", tk.END)
            details.insert(tk.END, text)
            details.configure(state="disabled")

        lb.bind("<<ListboxSelect>>", _on_pick)
        if uids:
            lb.selection_set(0)
            _on_pick()
