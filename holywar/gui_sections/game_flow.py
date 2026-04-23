from __future__ import annotations

import json
import random
import tkinter as tk
from tkinter import filedialog, messagebox

from holywar.ai.simple_ai import choose_action
from holywar.core.engine import GameEngine
from holywar.data.deck_builder import available_premade_decks, get_premade_label


class GUIGameFlowMixin:
    """Turn flow, AI loop, chain priority and persistence actions."""

    def show_main_menu(self) -> None:
        self.game_screen.pack_forget()
        self.deck_manager_frame.pack_forget()
        self.main_menu_frame.pack(fill="both", expand=True)

    def show_game_screen(self) -> None:
        self.main_menu_frame.pack_forget()
        self.deck_manager_frame.pack_forget()
        self.game_screen.pack(fill="both", expand=True)

    def show_deck_manager(self) -> None:
        self.main_menu_frame.pack_forget()
        self.game_screen.pack_forget()
        self.deck_manager_frame.pack(fill="both", expand=True)
        self._sync_deck_filter_expansions()
        self._deck_manager_reload_user_decks()

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
        self.engine.choose_battle_survival_from_graveyard = self._choose_battle_survival_from_graveyard
        self.engine.choose_auto_play_slot_from_draw = self._choose_auto_play_slot_from_draw
        self.rng = random.Random(self.seed)
        self.last_log_idx = 0
        self.turn_started = False
        self.ai_running = False
        self.chain_active = False
        self.chain_priority_idx = 0
        self.chain_pass_count = 0
        self._reveal_prompt_open = False
        self._reveal_prompt_last_uid = ""
        self._post_reveal_chain_actor = None
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

    def _choose_battle_survival_from_graveyard(
        self,
        player_idx: int,
        source_uid: str,
        candidate_uids: list[str],
    ) -> str | None:
        if self.engine is None:
            return None

        if not candidate_uids:
            return None

        # Se il controllore è AI, usa fallback automatico sulla prima carta valida.
        if self._is_ai_player(player_idx):
            return candidate_uids[0]

        source_inst = self.engine.state.instances.get(source_uid)
        source_name = source_inst.definition.name if source_inst is not None else "questa carta"
        player_name = self.engine.state.players[player_idx].name

        wants = messagebox.askyesno(
            "Effetto di sopravvivenza",
            f"{player_name}: {source_name} è stato sconfitto in battaglia.\n\n"
            "Vuoi attivare il suo effetto per annullare la distruzione?",
        )
        if not wants:
            return None

        choices: list[tuple[str, str]] = []
        for g_uid in candidate_uids:
            inst = self.engine.state.instances.get(g_uid)
            if inst is None:
                continue
            label = inst.definition.name
            choices.append((label, g_uid))

        if not choices:
            return None

        canceled, selected = self._open_board_target_picker(
            title="Scegli carta da scomunicare",
            prompt="Seleziona quale carta del tuo cimitero scomunicare per salvare Thor.",
            choices=choices,
            allow_multi=False,
            min_targets=1,
            max_targets=1,
            allow_none=False,
            allow_manual=False,
            card_uid=source_uid,
        )
        if canceled or not selected:
            return None

        return selected

    def _choose_auto_play_slot_from_draw(
        self,
        player_idx: int,
        source_uid: str,
        slot_tokens: list[str],
    ) -> str | None:
        if self.engine is None:
            return slot_tokens[0] if slot_tokens else None
        if not slot_tokens:
            return None

        # AI side: deterministic first available slot.
        if self._is_ai_player(player_idx):
            return slot_tokens[0]

        inst = self.engine.state.instances.get(source_uid)
        card_name = inst.definition.name if inst is not None else "questa carta"
        choices: list[tuple[str, str]] = []
        for token in slot_tokens:
            side = "Attacco" if token.startswith("a") else "Difesa"
            label = f"{side} {token[1:]}"
            choices.append((label, token))

        canceled, selected = self._open_board_target_picker(
            title=f"{card_name} - Posizionamento",
            prompt=f"Scegli dove posizionare {card_name}.",
            choices=choices,
            allow_multi=False,
            min_targets=1,
            max_targets=1,
            allow_none=False,
            allow_manual=False,
            card_uid=source_uid,
        )
        if canceled or not selected:
            return slot_tokens[0]
        return str(selected).strip().lower()

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
