from __future__ import annotations

from typing import Any
import tkinter as tk
from tkinter import messagebox, ttk

from holywar.core.engine import GameEngine
from holywar.core.state import GameState
from holywar.effects.runtime import runtime_cards, _norm
from holywar.effects.card_scripts_loader import iter_card_scripts
from holywar.scripting_api import RuleEventContext


class GUITargetingMixin:
    """Targeting and board-picker logic used by play/activate flows."""

    def _clone_engine(self) -> GameEngine | None:
        if self.engine is None:
            return None
        if self._sim_state_snapshot is None:
            snapshot = self.engine.state.to_dict()
            # The right-click preview does not need historical logs; skipping
            # them keeps per-click simulation clones cheaper in long matches.
            snapshot["logs"] = []
            self._sim_state_snapshot = snapshot
        cloned_state = GameState.from_dict(self._sim_state_snapshot)
        return GameEngine(cloned_state, seed=self.seed)

    def _can_attack_target(self, player_idx: int, from_slot: int, target_slot: int | None) -> bool:
        sim = self._clone_engine()
        if sim is None:
            return False
        res = sim.attack(player_idx, from_slot, target_slot)
        return bool(res.ok and self._is_effective_result_message(res.message))

    def _can_activate_target(self, player_idx: int, source: str, target: str | None) -> bool:
        sim = self._clone_engine()
        if sim is None:
            return False
        res = sim.activate_ability(player_idx, source, target)
        return bool(res.ok and self._is_effective_result_message(res.message))

    def _can_play_target(self, player_idx: int, hand_idx: int, target: str | None, quick: bool = False) -> bool:
        sim = self._clone_engine()
        if sim is None:
            return False
        if quick:
            res = sim.quick_play(player_idx, hand_idx, target)
        else:
            res = sim.play_card(player_idx, hand_idx, target)
        return bool(res.ok and self._is_effective_result_message(res.message))

    def _is_effective_result_message(self, msg: str | None) -> bool:
        text = (msg or "").lower().strip()
        if not text:
            return False
        blocked_markers = [
            "nessun bersaglio",
            "bersaglio non valido",
            "non valida",
            "non valido",
            "non disponibile",
            "impossibile",
            "devi selezionare",
            "scegli un artefatto",
            "gia usata",
            "nessun effetto scriptato",
            "nessun effetto attivabile",
            "effetto registrato",
            "in sviluppo",
            "effetto non trascritto",
            "legacy disabilitato",
        ]
        return not any(m in text for m in blocked_markers)

    def _candidate_slot_tokens(self) -> list[str]:
        return ["a1", "a2", "a3", "d1", "d2", "d3", "r1", "r2", "r3", "r4", "b"]

    def _split_board_token(self, token: str) -> tuple[str | None, str]:
        raw = str(token or "").strip()
        if ":" not in raw:
            return (None, raw)

        side, base = raw.split(":", 1)
        side_key = side.strip().lower()
        base = base.strip()

        if side_key in {"s", "self", "me", "own", "owner", "controller"}:
            return ("own", base)
        if side_key in {"o", "opp", "enemy", "opponent", "other"}:
            return ("enemy", base)
        return (None, raw)

    def _card_script(self, uid: str):
        if self.engine is None:
            return None
        card_name = self.engine.state.instances[uid].definition.name
        return runtime_cards.get_script(card_name)

    def _raw_card_script(self, uid: str) -> dict:
        if self.engine is None:
            return {}

        inst = self.engine.state.instances.get(uid)
        if inst is None:
            return {}

        wanted = _norm(inst.definition.name)

        for card_name, spec in iter_card_scripts():
            if _norm(card_name) == wanted:
                return spec or {}

        return {}

    def _manual_play_target_actions(self, uid: str):
        raw = self._raw_card_script(uid)
        script = self._card_script(uid)
        if not raw or script is None:
            return []
        if self.engine is None:
            return []
        source_inst = self.engine.state.instances.get(uid)
        if source_inst is None:
            return []
        owner_idx = int(source_inst.owner)

        raw_actions = raw.get("on_play_actions", [])
        out = []
        for i, raw_action in enumerate(raw_actions):
            if i >= len(script.on_play_actions):
                break
            if "target" not in raw_action:
                continue
            action_spec = script.on_play_actions[i]
            if action_spec.condition and not runtime_cards._eval_condition_node(  # noqa: SLF001
                RuleEventContext(engine=self.engine, event="on_play", player_idx=owner_idx, payload={"card": uid}),
                owner_idx,
                action_spec.condition,
            ):
                continue
            raw_target = raw_action.get("target", {}) or {}
            t = action_spec.target
            ttype = str(t.type or "").strip().lower()
            requires_manual = any(
                key in raw_target
                for key in ("zone", "zones", "card_filter", "min_targets", "max_targets", "max_targets_from", "owner")
            )
            if ttype in {"selected_target", "selected_targets"} and requires_manual:
                out.append((i, t))
        return out

    def _first_play_target_spec(self, uid: str):
        actions = self._manual_play_target_actions(uid)
        if not actions:
            return None
        return actions[0][1]

    def _play_targeting_mode(self, uid: str) -> str:
        script = self._card_script(uid)
        if script is None:
            return "auto"
        return str(script.play_targeting or "auto").strip().lower() or "auto"

    def _activate_targeting_mode(self, uid: str) -> str:
        script = self._card_script(uid)
        if script is None:
            return "auto"
        return str(script.activate_targeting or "auto").strip().lower() or "auto"

    def _play_owner_idx(self, uid: str) -> int:
        if self.engine is None:
            return 0
        script = self._card_script(uid)
        if script is None:
            return self.current_human_idx() or 0
        owner = str(getattr(script, "play_owner", "me") or "me").strip().lower()
        if owner in {"opponent", "enemy", "other"}:
            return 1 - (self.current_human_idx() or 0)
        return self.current_human_idx() or 0

    def _valid_play_targets(self, player_idx: int, hand_idx: int, uid: str, quick: bool) -> list[str]:
        if self.engine is None:
            return []
        candidates = self._guided_target_candidates(uid)
        if not candidates:
            return []
        out: list[str] = []
        for token in candidates:
            if self._can_play_target(player_idx, hand_idx, token, quick=quick):
                out.append(token)
        return out

    def _valid_attack_targets(self, player_idx: int, from_slot: int) -> list[int | None]:
        out: list[int | None] = []
        if self._can_attack_target(player_idx, from_slot, None):
            out.append(None)
        for slot in range(3):
            if self._can_attack_target(player_idx, from_slot, slot):
                out.append(slot)
        return out

    def _valid_activation_targets(self, player_idx: int, source: str, uid: str | None) -> list[str]:
        if self.engine is None:
            return []
        if uid is None:
            return []
        mode = self._activate_targeting_mode(uid)
        if mode == "board_card":
            candidates = self._board_activation_candidates(player_idx)
        elif mode in {"auto", "guided", "manual"}:
            target_spec = self._first_activate_target_spec(uid)
            if target_spec is None:
                return []
            candidates = self._guided_target_candidates_for_spec(uid, target_spec)
        else:
            return []
        out: list[str] = []
        for token in dict.fromkeys(candidates):
            if self._can_activate_target(player_idx, source, token):
                out.append(token)
        return out

    def _activation_has_any_valid_option(self, player_idx: int, source: str) -> bool:
        if self.engine is None:
            return False
        uid = self.engine.resolve_board_uid(player_idx, source)
        if uid is None:
            return False

        script = self._card_script(uid)
        if script is None:
            return False

        mode = str(getattr(script, "on_activate_mode", "auto") or "auto").strip().lower()
        if mode not in {"scripted", "custom"}:
            return False
        if not getattr(script, "on_activate_actions", None):
            return False

        inst = self.engine.state.instances.get(uid)
        if inst is not None:
            if runtime_cards.is_activate_once_per_turn(inst.definition.name) and not self.engine.can_activate_once_per_turn(uid):
                return False

        if self._can_activate_target(player_idx, source, None):
            return True
        return bool(self._valid_activation_targets(player_idx, source, uid))

    def _clear_slot_highlights(self) -> None:
        for widget, old in self._slot_highlights:
            try:
                widget.configure(**old)
            except tk.TclError:
                pass
        self._slot_highlights.clear()

    def _is_board_token(self, token: str) -> bool:
        _side, base = self._split_board_token(token)

        if base == "b":
            return True
        if len(base) != 2 or not base[1].isdigit():
            return False
        if base[0] in {"a", "d"}:
            return 1 <= int(base[1]) <= 3
        if base[0] == "r":
            return 1 <= int(base[1]) <= 4
        return False

    def _card_target_hints(self, card_uid: str | None) -> tuple[bool, bool]:
        if self.engine is None or card_uid is None:
            return (False, False)

        mode = self._play_targeting_mode(card_uid)
        if mode == "own_saint":
            return (True, False)
        if mode == "opponent_saint":
            return (False, True)
        if mode == "board_card":
            return (True, True)

        # Supporto ai target guided sul campo
        target = self._first_play_target_spec(card_uid)
        if target is not None:
            zones = [z.lower().strip() for z in (target.zones or []) if str(z).strip()]
            if not zones:
                zones = [str(target.zone or "field").strip().lower()]

            if "field" in zones:
                owner_key = str(target.owner or "me").strip().lower()
                if owner_key in {"any", "both", "all", "either"}:
                    return (True, True)
                if owner_key in {"me", "owner", "controller"}:
                    return (True, False)
                if owner_key in {"opponent", "enemy"}:
                    return (False, True)

        return (False, False)

    def _resolve_highlight_widget(
        self,
        token: str,
        *,
        own_idx: int,
        side_hint: str = "auto",
        card_uid: str | None = None,
    ) -> tk.Widget | None:
        if self.engine is None:
            return None
        enemy_idx = 1 - own_idx
        own = self.engine.state.players[own_idx]
        enemy = self.engine.state.players[enemy_idx]
        raw_token = str(token or "").strip().lower()
        explicit_side: str | None = None
        if ":" in raw_token:
            side, code = raw_token.split(":", 1)
            if side in {"s", "self", "me", "own", "owner", "controller"}:
                explicit_side = "own"
                token = code
            elif side in {"o", "opp", "enemy", "opponent", "other"}:
                explicit_side = "enemy"
                token = code
        if side_hint not in {"auto", "own", "enemy"}:
            side_hint = "auto"
        wants_own, wants_opp = self._card_target_hints(card_uid)
        if explicit_side is not None:
            side_hint = explicit_side
        if side_hint == "auto":
            if wants_own and not wants_opp:
                side_hint = "own"
            elif wants_opp and not wants_own:
                side_hint = "enemy"

        # UID diretto: risolvi la carta sul campo senza ambiguita di slot/sponda.
        if token in self.engine.state.instances:
            for i, c_uid in enumerate(own.attack):
                if c_uid == token:
                    return self.own_attack[i]
            for i, c_uid in enumerate(own.defense):
                if c_uid == token:
                    return self.own_defense[i]
            for i, c_uid in enumerate(own.artifacts):
                if c_uid == token:
                    return self.own_artifacts[i]
            if own.building == token:
                return self.own_building
            for i, c_uid in enumerate(enemy.attack):
                if c_uid == token:
                    return self.enemy_attack[i]
            for i, c_uid in enumerate(enemy.defense):
                if c_uid == token:
                    return self.enemy_defense[i]
            for i, c_uid in enumerate(enemy.artifacts):
                if c_uid == token:
                    return self.enemy_artifacts[i]
            if enemy.building == token:
                return self.enemy_building
            return None

        if token.startswith("a") and len(token) == 2 and token[1].isdigit():
            i = int(token[1]) - 1
            if not (0 <= i < 3):
                return None
            if side_hint == "own":
                return self.own_attack[i] if own.attack[i] is not None else None
            if side_hint == "enemy":
                return self.enemy_attack[i] if enemy.attack[i] is not None else None
            if enemy.attack[i] is not None:
                return self.enemy_attack[i]
            if own.attack[i] is not None:
                return self.own_attack[i]
            return None
        if token.startswith("d") and len(token) == 2 and token[1].isdigit():
            i = int(token[1]) - 1
            if not (0 <= i < 3):
                return None
            if side_hint == "own":
                return self.own_defense[i] if own.defense[i] is not None else None
            if side_hint == "enemy":
                return self.enemy_defense[i] if enemy.defense[i] is not None else None
            if enemy.defense[i] is not None:
                return self.enemy_defense[i]
            if own.defense[i] is not None:
                return self.own_defense[i]
            return None
        if token.startswith("r") and len(token) == 2 and token[1].isdigit():
            i = int(token[1]) - 1
            if not (0 <= i < 4):
                return None
            if side_hint == "own":
                return self.own_artifacts[i] if own.artifacts[i] is not None else None
            if side_hint == "enemy":
                return self.enemy_artifacts[i] if enemy.artifacts[i] is not None else None
            if enemy.artifacts[i] is not None:
                return self.enemy_artifacts[i]
            if own.artifacts[i] is not None:
                return self.own_artifacts[i]
            return None

        if token == "b":
            if side_hint == "own":
                return self.own_building if own.building is not None else None
            if side_hint == "enemy":
                return self.enemy_building if enemy.building is not None else None
            if enemy.building is not None:
                return self.enemy_building
            if own.building is not None:
                return self.own_building
            return None
        return None

    def _set_slot_highlights(
        self,
        targets: list[str],
        *,
        selected_targets: list[str] | None = None,
        card_uid: str | None = None,
        side_hint: str = "auto",
    ) -> None:
        self._clear_slot_highlights()
        if self.engine is None:
            return
        own_idx = self.current_human_idx() or 0
        selected = set(selected_targets or [])
        for token in targets:
            widget = self._resolve_highlight_widget(token, own_idx=own_idx, side_hint=side_hint, card_uid=card_uid)
            if widget is None:
                continue
            old: dict[str, str] = {}
            try:
                if isinstance(widget, tk.Button):
                    old["relief"] = str(widget.cget("relief"))
                    old["borderwidth"] = str(widget.cget("borderwidth"))
                    if token in selected:
                        widget.configure(relief="solid", borderwidth=4)
                    else:
                        widget.configure(relief="ridge", borderwidth=2)
                elif isinstance(widget, (ttk.Label, tk.Label)):
                    # ttk.Label non supporta bene border highlight: usa marker testuale.
                    old["text"] = str(widget.cget("text"))
                    marker = "[X] " if token in selected else "[ ] "
                    base_text = old["text"]
                    if base_text.startswith("[X] ") or base_text.startswith("[ ] "):
                        base_text = base_text[4:]
                    widget.configure(text=marker + base_text)
                else:
                    continue
                self._slot_highlights.append((widget, old))
            except tk.TclError:
                # ttk widgets do not always support relief/borderwidth in all themes.
                continue

    def _open_board_target_picker(
        self,
        *,
        title: str,
        prompt: str,
        candidates: list[str] | None = None,
        choices: list[tuple[str, str]] | None = None,
        allow_multi: bool = False,
        min_targets: int = 0,
        max_targets: int | None = None,
        allow_none: bool = True,
        allow_manual: bool = False,
        card_uid: str | None = None,
        side_hint: str = "auto",
        preserve_selection_order: bool = False,
    ) -> tuple[bool, str | None]:
        if self.engine is None:
            return (True, None)

        own_idx = self.current_human_idx() or 0

        if choices is None:
            choices = []
            for token in (candidates or []):
                choices.append((self._format_guided_candidate(token, own_idx), token))

        normalized_choices: list[tuple[str, str]] = []
        seen_tokens: set[str] = set()
        for label, token in choices:
            token = str(token).strip()
            if not token or token in seen_tokens:
                continue
            normalized_choices.append((label, token))
            seen_tokens.add(token)

        if not normalized_choices and not allow_manual and not allow_none:
            return (True, None)

        board_tokens: list[str] = []
        for _label, token in normalized_choices:
            if self._resolve_highlight_widget(token, own_idx=own_idx, side_hint=side_hint, card_uid=card_uid) is not None:
                board_tokens.append(token)

        selected_tokens: list[str] = []
        result: dict[str, str | None] = {"value": ""}
        bindings: list[tuple[tk.Widget, str]] = []

        win = tk.Toplevel(self)
        win.title(title)
        self._center_toplevel(win, 700, 560)
        win.transient(self)
        p = self._target_picker_palette
        win.configure(bg=p["bg"])

        container = ttk.Frame(win, style="TargetPicker.TFrame", padding=(10, 10))
        container.pack(fill="both", expand=True)

        ttk.Label(container, text=prompt, wraplength=660, style="TargetPicker.TLabel").pack(anchor="w", pady=(0, 4))

        if allow_multi:
            lim = ""
            if min_targets > 0 and max_targets is not None and min_targets == max_targets:
                lim = f" (seleziona esattamente {min_targets})"
            elif max_targets is not None:
                lim = f" (min {min_targets}, max {max_targets})"
            ttk.Label(
                container,
                text=f"Puoi selezionare dalla lista o cliccando sul campo{lim}.",
                style="TargetPicker.Muted.TLabel",
            ).pack(anchor="w", pady=(0, 4))
        else:
            ttk.Label(
                container,
                text="Puoi selezionare dalla lista o cliccando sul campo.",
                style="TargetPicker.Muted.TLabel",
            ).pack(anchor="w", pady=(0, 4))

        counter_var = tk.StringVar(value="")
        selected_var = tk.StringVar(value="Nessun bersaglio selezionato.")
        ttk.Label(container, textvariable=counter_var, style="TargetPicker.Counter.TLabel").pack(anchor="w")
        ttk.Label(container, textvariable=selected_var, wraplength=660, style="TargetPicker.TLabel").pack(anchor="w", pady=(4, 8))

        list_wrap = ttk.Frame(container, style="TargetPicker.Surface.TFrame")
        list_wrap.pack(fill="both", expand=True)
        list_wrap.columnconfigure(0, weight=1)
        list_wrap.rowconfigure(0, weight=1)
        lb = tk.Listbox(list_wrap, selectmode=("multiple" if allow_multi else "browse"))
        lb.grid(row=0, column=0, sticky="nsew")
        self._apply_target_picker_listbox_theme(lb)
        lb_scroll = ttk.Scrollbar(list_wrap, orient="vertical", command=lb.yview, style="TargetPicker.Vertical.TScrollbar")
        lb_scroll.grid(row=0, column=1, sticky="ns")
        lb.configure(yscrollcommand=lb_scroll.set)

        for label, _token in normalized_choices:
            lb.insert(tk.END, label)

        token_to_index = {token: i for i, (_label, token) in enumerate(normalized_choices)}

        manual_var = tk.StringVar(value="")
        if allow_manual:
            row = ttk.Frame(container, style="TargetPicker.TFrame")
            row.pack(fill="x", pady=(8, 0))
            ttk.Label(row, text="Valore manuale (opzionale):", style="TargetPicker.TLabel").pack(side="left")
            ttk.Entry(row, textvariable=manual_var, style="TargetPicker.TEntry").pack(side="left", fill="x", expand=True, padx=6)

        btn_bar = ttk.Frame(container, style="TargetPicker.TFrame")
        btn_bar.pack(fill="x", pady=(8, 0))
        btn_ok = ttk.Button(btn_bar, text="OK", style="TargetPicker.Primary.TButton")
        btn_ok.pack(side="left")

        def _selection_ok() -> bool:
            raw_manual = manual_var.get().strip() if allow_manual else ""
            if raw_manual:
                return True
            count = len(selected_tokens)
            upper = max_targets if max_targets is not None else (9999 if allow_multi else 1)
            return min_targets <= count <= upper

        def _sync_listbox() -> None:
            lb.selection_clear(0, tk.END)
            for token in selected_tokens:
                idx = token_to_index.get(token)
                if idx is not None:
                    lb.selection_set(idx)

        def _refresh_state() -> None:
            upper_txt = str(max_targets) if max_targets is not None else ("n" if allow_multi else "1")
            counter_var.set(f"Selezionati {len(selected_tokens)} bersagli (min {min_targets}, max {upper_txt})")

            if selected_tokens:
                labels = [self._format_guided_candidate(tok, own_idx) for tok in selected_tokens]
                if preserve_selection_order:
                    numbered = [f"{i + 1}) {label}" for i, label in enumerate(labels)]
                    selected_var.set("Ordine selezionato: " + " | ".join(numbered))
                else:
                    selected_var.set("Selezione: " + " | ".join(labels))
            else:
                selected_var.set("Nessun bersaglio selezionato.")

            _sync_listbox()
            self._set_slot_highlights(board_tokens, selected_targets=selected_tokens, card_uid=card_uid, side_hint=side_hint)
            btn_ok.configure(state=("normal" if _selection_ok() else "disabled"))

        def _set_single(token: str) -> None:
            selected_tokens.clear()
            selected_tokens.append(token)
            _refresh_state()

        def _toggle_token(token: str):
            if allow_multi:
                if token in selected_tokens:
                    selected_tokens.remove(token)
                else:
                    if max_targets is not None and len(selected_tokens) >= max_targets:
                        return "break"
                    selected_tokens.append(token)
            else:
                if token in selected_tokens:
                    selected_tokens.clear()
                else:
                    _set_single(token)
                    return "break"
            _refresh_state()
            return "break"

        def _on_listbox_select(_event=None):
            idxs = list(lb.curselection())
            tokens = [normalized_choices[i][1] for i in idxs]

            if not allow_multi and len(tokens) > 1:
                tokens = tokens[:1]

            if max_targets is not None and len(tokens) > max_targets:
                tokens = tokens[:max_targets]

            if allow_multi and preserve_selection_order:
                previous = list(selected_tokens)

                # rimuovi quelli deselezionati
                selected_tokens[:] = [tok for tok in selected_tokens if tok in tokens]

                # aggiungi in coda i nuovi selezionati, nell'ordine in cui compaiono
                for tok in tokens:
                    if tok not in selected_tokens:
                        if max_targets is not None and len(selected_tokens) >= max_targets:
                            break
                        selected_tokens.append(tok)

                # se l'utente ha fatto una selezione "pulita" da zero
                if not previous and not selected_tokens and tokens:
                    selected_tokens.extend(tokens[:max_targets] if max_targets is not None else tokens)
            else:
                selected_tokens.clear()
                selected_tokens.extend(tokens)

            _refresh_state()

        lb.bind("<<ListboxSelect>>", _on_listbox_select)

        for token in board_tokens:
            widget = self._resolve_highlight_widget(token, own_idx=own_idx, side_hint=side_hint, card_uid=card_uid)
            if widget is None:
                continue
            func_id = widget.bind("<Button-1>", lambda e, t=token: _toggle_token(t), add="+")
            bindings.append((widget, func_id))

        def _cleanup() -> None:
            for widget, func_id in bindings:
                try:
                    widget.unbind("<Button-1>", func_id)
                except tk.TclError:
                    pass
            self._clear_slot_highlights()

        def _ok() -> None:
            raw_manual = manual_var.get().strip() if allow_manual else ""
            if raw_manual:
                result["value"] = raw_manual
                _cleanup()
                win.destroy()
                return

            if not _selection_ok():
                if max_targets is not None and min_targets == max_targets:
                    messagebox.showwarning("Selezione non valida", f"Devi selezionare esattamente {min_targets} bersagli.")
                elif max_targets is not None:
                    messagebox.showwarning("Selezione non valida", f"Seleziona tra {min_targets} e {max_targets} bersagli.")
                else:
                    messagebox.showwarning("Selezione non valida", f"Seleziona almeno {min_targets} bersagli.")
                return

            if not selected_tokens:
                result["value"] = None if allow_none else ""
            else:
                result["value"] = ",".join(selected_tokens)

            _cleanup()
            win.destroy()

        def _no_target() -> None:
            result["value"] = None
            _cleanup()
            win.destroy()

        def _cancel() -> None:
            result["value"] = ""
            _cleanup()
            win.destroy()

        btn_ok.configure(command=_ok)
        if allow_none:
            ttk.Button(btn_bar, text="Senza Target", command=_no_target, style="TargetPicker.TButton").pack(side="left", padx=6)
        ttk.Button(btn_bar, text="Annulla", command=_cancel, style="TargetPicker.TButton").pack(side="left", padx=6)

        win.protocol("WM_DELETE_WINDOW", _cancel)
        _refresh_state()
        self.wait_window(win)
        return (result["value"] == "", result["value"])
