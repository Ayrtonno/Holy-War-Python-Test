from __future__ import annotations

import argparse
import random
import traceback
import tkinter as tk
from tkinter import messagebox, ttk

from holywar.cli import DEFAULT_JSON, ensure_cards
from holywar.core.engine import GameEngine
from holywar.data.deck_builder import (
    PREMADE_STORE_PATH,
    available_religions,
    register_premades_from_json,
)
from holywar.app_paths import appdata_dir
from holywar.gui_sections import GUIStylesMixin, GUIDeckManagerMixin, GUITargetingMixin, GUIGameFlowMixin, GUIGameViewMixin, GUIGameActionsMixin

# This module defines the `HolyWarGUI` class, which is the main graphical user interface for the Holy War game. It uses the Tkinter library to create a windowed application that allows players to interact with the game visually. The GUI includes features for starting new games, managing decks, displaying the game state, and handling player actions. The class also includes methods for building the user interface, updating the display based on the game state, and responding to user input. Additionally, there are functions for building a command-line argument parser and running the main application loop.
class HolyWarGUI(GUIStylesMixin, GUIDeckManagerMixin, GUITargetingMixin, GUIGameFlowMixin, GUIGameViewMixin, GUIGameActionsMixin, tk.Tk):
    def __init__(self, cards, seed: int | None, ai_delay: float) -> None:
        super().__init__()
        self.title("Holy War - Duel Board")
        self.geometry("1280x860")
        self.minsize(1180, 760)
        try:
            # Avvio in finestra massimizzata (fullscreen windowed).
            self.state("zoomed")
        except tk.TclError:
            try:
                self.attributes("-zoomed", True)
            except tk.TclError:
                pass
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
        self._reveal_prompt_open = False
        self._reveal_prompt_last_uid = ""
        self._post_reveal_chain_actor: int | None = None
        self._sim_state_snapshot: dict | None = None
        self.religions = religions
        self.premades_path = PREMADE_STORE_PATH
        self._deck_editor_selected_id: str | None = None
        self._deck_editor_cards: dict[str, int] = {}
        self._deck_candidates_sort_col = "nome"
        self._deck_candidates_sort_asc = True
        self._deck_current_sort_col = "nome"
        self._deck_current_sort_asc = True
        self._deck_candidates_value_filters: dict[str, set[str]] = {}
        self._deck_current_value_filters: dict[str, set[str]] = {}
        self._deck_candidates_rows_cache: list[dict] = []
        self._deck_current_rows_cache: list[dict] = []
        self._p1_deck_map: dict[str, str | None] = {}
        self._p2_deck_map: dict[str, str | None] = {}
        self.resource_name_labels: list[ttk.Label] = []
        self.resource_sin_labels: list[ttk.Label] = []
        self.resource_insp_labels: list[ttk.Label] = []
        self.resource_hand_labels: list[ttk.Label] = []
        self.resource_deck_labels: list[ttk.Label] = []
        self.resource_sin_bars: list[ttk.Progressbar] = []
        self._slot_highlights: list[tuple[tk.Widget, dict[str, str]]] = []
        self._replay_snapshots: list[dict[str, object]] = []
        self._replay_last_signature: str = ""
        self._replay_playback: bool = False
        self._replay_after_id: str | None = None
        self._replay_loaded_name: str = ""
        self._replay_loaded_snapshots: list[dict[str, object]] = []
        self._replay_index: int = 0
        self._replay_paused: bool = False
        self._replay_step_ms: int = 1000
        self._setup_deck_builder_styles()
        self._setup_game_styles()
        self._setup_target_picker_styles()
        self._load_premades_into_runtime()
        self._build_ui()
        self.show_main_menu()

    # Main game/deck screens layout and static widget wiring.
    def _build_ui(self) -> None:
        self.main_menu_frame = ttk.Frame(self)
        self.game_screen = ttk.Frame(self)
        self.deck_manager_frame = ttk.Frame(self)
        self.replay_manager_frame = ttk.Frame(self)

        title = ttk.Label(self.main_menu_frame, text="Holy War", font=("Segoe UI", 26, "bold"))
        title.pack(pady=(90, 24))
        ttk.Button(self.main_menu_frame, text="Gioca", command=self.show_game_screen, width=28).pack(pady=10)
        ttk.Button(
            self.main_menu_frame,
            text="Crea/Modifica deck",
            command=self.show_deck_manager,
            width=28,
        ).pack(pady=10)
        ttk.Button(
            self.main_menu_frame,
            text="Replay",
            command=self.show_replay_manager,
            width=28,
        ).pack(pady=10)

        top = ttk.Frame(self.game_screen)
        top.pack(fill="x", padx=8, pady=8)
        self.game_top_frame = top

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
        self.game_actions_frame = actions
        ttk.Button(actions, text="Menu", command=self.show_main_menu).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Nuova Partita", command=self.new_game).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Fine Turno", command=self.end_turn).pack(side="left", padx=4)
        ttk.Button(actions, text="Salva", command=self.save_game).pack(side="left", padx=4)
        ttk.Button(actions, text="Salva Replay", command=self.save_replay).pack(side="left", padx=4)
        ttk.Button(actions, text="Stop Replay", command=self.stop_replay_playback).pack(side="left", padx=4)
        ttk.Button(actions, text="Esporta Log", command=self.export_log).pack(side="left", padx=4)
        ttk.Button(actions, text="Catena SI", command=lambda: self.set_chain_enabled(True)).pack(side="left", padx=(12, 4))
        ttk.Button(actions, text="Catena NO", command=lambda: self.set_chain_enabled(False)).pack(side="left", padx=4)
        ttk.Button(actions, text="OK Catena", command=self.chain_ok).pack(side="left", padx=4)
        ttk.Button(actions, text="Deck", command=lambda: self.open_debug_zone("deck")).pack(side="left", padx=(12, 4))
        ttk.Button(actions, text="Cimitero", command=lambda: self.open_debug_zone("graveyard")).pack(side="left", padx=4)
        ttk.Button(actions, text="Scomunicate", command=lambda: self.open_debug_zone("excommunicated")).pack(side="left", padx=4)
        ttk.Button(actions, text="Innate", command=lambda: self.open_debug_zone("innate")).pack(side="left", padx=4)

        top.columnconfigure(7, weight=1)
        top.columnconfigure(13, weight=1)
        self.p1_rel_combo.bind("<<ComboboxSelected>>", lambda _e: self.update_premade_options())
        self.p2_rel_combo.bind("<<ComboboxSelected>>", lambda _e: self.update_premade_options())
        self.update_premade_options()

        ttk.Label(self.game_screen, textvariable=self.status_var).pack(fill="x", padx=8)
        self.replay_controls_frame = ttk.Frame(self.game_screen)
        self.replay_controls_frame.pack(fill="x", padx=8, pady=(4, 0))
        self.replay_controls_frame.pack_forget()
        ttk.Button(self.replay_controls_frame, text="Esci Replay", command=self.exit_replay_to_manager).pack(side="left", padx=(0, 8))
        self.replay_playpause_btn = ttk.Button(self.replay_controls_frame, text="Pausa", command=self.replay_toggle_pause)
        self.replay_playpause_btn.pack(side="left", padx=4)
        ttk.Button(self.replay_controls_frame, text="Velocita -", command=lambda: self.replay_change_speed(1.25)).pack(side="left", padx=4)
        ttk.Button(self.replay_controls_frame, text="Velocita +", command=lambda: self.replay_change_speed(0.8)).pack(side="left", padx=4)
        ttk.Label(self.replay_controls_frame, text="Salta a turno").pack(side="left", padx=(12, 4))
        self.replay_jump_turn_var = tk.StringVar(value="")
        self.replay_jump_turn_entry = ttk.Entry(self.replay_controls_frame, textvariable=self.replay_jump_turn_var, width=8)
        self.replay_jump_turn_entry.pack(side="left", padx=4)
        ttk.Button(self.replay_controls_frame, text="Vai", command=self.replay_jump_to_turn).pack(side="left", padx=4)
        self.replay_speed_label = ttk.Label(self.replay_controls_frame, text="1000 ms/step")
        self.replay_speed_label.pack(side="left", padx=(12, 0))

        center = ttk.Frame(self.game_screen)
        center.pack(fill="both", expand=True, padx=8, pady=8)

        board = ttk.Frame(center)
        board.pack(side="left", fill="both", expand=True)

        self.info_label = ttk.Label(board, text="Nessuna partita")
        self.info_label.pack(anchor="w", pady=4, fill="x")

        resource_bar = ttk.Frame(board)
        resource_bar.pack(fill="x", pady=(0, 6))
        self._build_resource_panel(resource_bar, "TU")
        self._build_resource_panel(resource_bar, "AVVERSARIO")

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

        # Slot click bindings (right-click for actions, left-click for details).
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
        self.hand_list = tk.Listbox(hand_frame, height=10)
        self.hand_list.pack(fill="both", expand=True, side="left")
        scroll = ttk.Scrollbar(hand_frame, command=self.hand_list.yview)
        self.hand_list.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.hand_list.bind("<Button-3>", self.on_hand_right_click)
        self.hand_list.bind("<<ListboxSelect>>", self.on_hand_select)
        self.hand_list.bind("<Double-Button-1>", lambda _e: self.play_selected_card())

        detail_frame = ttk.LabelFrame(board, text="Dettaglio Carta")
        detail_frame.pack(fill="both", expand=True, pady=4)
        self.card_detail_text = tk.Text(detail_frame, wrap="word", height=9)
        self.card_detail_text.pack(fill="both", expand=True)
        self.card_detail_text.configure(state="disabled")

        log_frame = ttk.LabelFrame(center, text="Log Partita")
        log_frame.pack(fill="both", expand=True)
        self.log_text = tk.Text(log_frame, wrap="word", width=58)
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")
        self.bind("<Return>", lambda _e: self.play_selected_card())

        self.game_screen.configure(style="Game.TFrame")
        self.configure(bg=self._game_palette["bg"])
        self._apply_game_theme(self.game_screen)

        self._build_deck_manager_ui()
        self._build_replay_manager_ui()

    def _build_replay_manager_ui(self) -> None:
        top = ttk.Frame(self.replay_manager_frame)
        top.pack(fill="x", padx=10, pady=10)
        ttk.Button(top, text="Menu", command=self.show_main_menu, width=18).pack(side="left")
        ttk.Button(top, text="Ricarica", command=self._replay_manager_reload, width=18).pack(side="left", padx=6)
        ttk.Button(top, text="Riproduci", command=self.replay_play_selected, width=18).pack(side="left", padx=6)
        ttk.Button(top, text="Rinomina Replay", command=self.replay_rename_selected, width=18).pack(side="left", padx=6)
        ttk.Button(top, text="Elimina Replay", command=self.replay_delete_selected, width=18).pack(side="left", padx=6)

        list_frame = ttk.LabelFrame(self.replay_manager_frame, text="Replay salvati")
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.replay_list = tk.Listbox(list_frame, height=18)
        self.replay_list.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(list_frame, command=self.replay_list.yview)
        self.replay_list.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.replay_list.bind("<Double-Button-1>", lambda _e: self.replay_play_selected())

        detail = ttk.LabelFrame(self.replay_manager_frame, text="Dettaglio")
        detail.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.replay_detail_text = tk.Text(detail, wrap="word", height=10)
        self.replay_detail_text.pack(fill="both", expand=True)
        self.replay_detail_text.configure(state="disabled")
        self.replay_list.bind("<<ListboxSelect>>", self._replay_on_select)

# This function builds the command-line argument parser for the application. It defines various arguments that can be passed when launching the application, such as the path to the deck Excel file, the path to the cards JSON cache, the path to custom premade decks JSON, a random seed for game initialization, and a delay for AI actions. This allows users to customize their experience when starting the application from the command line.
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Holy War - GUI MVP")
    parser.add_argument("--deck-xlsx", type=str, default=None, help="Percorso a Holy War.xlsx")
    parser.add_argument("--cards-json", type=str, default=str(DEFAULT_JSON), help="Cache JSON carte")
    parser.add_argument("--premades-json", type=str, default=None, help="Importa deck premade custom da JSON")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--ai-delay", type=float, default=2.0)
    return parser

# CLI entrypoint for launching the desktop GUI app.
def main() -> None:
    try:
        parser = build_parser()
        args = parser.parse_args()
        if args.premades_json:
            register_premades_from_json(args.premades_json)
        cards = ensure_cards(args)
        app = HolyWarGUI(cards, seed=args.seed, ai_delay=args.ai_delay)
        app.mainloop()
    except Exception as exc:
        try:
            log_dir = appdata_dir()
            log_dir.mkdir(parents=True, exist_ok=True)
            err_path = log_dir / "startup_error.log"
            err_path.write_text(traceback.format_exc(), encoding="utf-8")
            messagebox.showerror("Holy War - Errore avvio", f"{exc}\n\nLog: {err_path}")
        except Exception:
            raise

if __name__ == "__main__":
    main()
