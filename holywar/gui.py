from __future__ import annotations

import argparse
import json
import random
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from holywar.ai.simple_ai import choose_action
from holywar.cli import DEFAULT_JSON, ensure_cards
from holywar.core.engine import GameEngine
from holywar.core.state import GameState
from holywar.effects.runtime import runtime_cards, _norm
from holywar.effects.card_scripts_loader import iter_card_scripts
from holywar.scripting_api import RuleEventContext
from holywar.data.deck_builder import (
    PREMADE_STORE_PATH,
    available_premade_decks,
    available_religions,
    get_premade_label,
    register_premades_from_json,
    reset_runtime_premades,
    runtime_premade_decks,
)
from holywar.app_paths import appdata_dir


def _card_aliases(definition) -> list[str]:
    raw_aliases = getattr(definition, "aliases", []) or []
    if isinstance(raw_aliases, str):
        return [part.strip() for part in raw_aliases.split(",") if part.strip()]
    return [str(alias).strip() for alias in raw_aliases if str(alias).strip()]


def _card_name_variants(definition) -> set[str]:
    variants = {_norm(definition.name)}
    variants.update(_norm(alias) for alias in _card_aliases(definition))
    return {v for v in variants if v}


def _card_name_haystack(definition) -> str:
    parts = [definition.name, *_card_aliases(definition)]
    return " ".join(_norm(part) for part in parts if str(part).strip())


class HolyWarGUI(tk.Tk):
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
        self._setup_deck_builder_styles()
        self._load_premades_into_runtime()
        self._build_ui()
        self.show_main_menu()

    def _setup_deck_builder_styles(self) -> None:
        self._deck_palette = {
            "bg": "#f3f7fc",
            "surface": "#ffffff",
            "surface_alt": "#f7fbff",
            "line": "#d6e2f0",
            "text": "#1f2d3d",
            "muted": "#5f748c",
            "accent": "#0078d4",
            "accent_soft": "#e8f2ff",
        }
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        p = self._deck_palette
        style.configure("DeckRoot.TFrame", background=p["bg"])
        style.configure("DeckSurface.TFrame", background=p["surface"])
        style.configure("DeckHero.TFrame", background=p["bg"])
        style.configure("DeckHeroTitle.TLabel", background=p["bg"], foreground=p["text"], font=("Segoe UI Semibold", 18))
        style.configure("DeckHeroSub.TLabel", background=p["bg"], foreground=p["muted"], font=("Segoe UI", 10))
        style.configure("DeckCard.TLabelframe", background=p["surface"], bordercolor=p["line"], borderwidth=1, relief="solid")
        style.configure("DeckCard.TLabelframe.Label", background=p["bg"], foreground=p["text"], font=("Segoe UI Semibold", 10))
        style.configure("DeckText.TLabel", background=p["surface"], foreground=p["text"], font=("Segoe UI", 10))
        style.configure("DeckMuted.TLabel", background=p["surface"], foreground=p["muted"], font=("Segoe UI", 9))
        style.configure("DeckTitle.TLabel", background=p["surface"], foreground=p["text"], font=("Segoe UI", 9))
        style.configure("Deck.TEntry", fieldbackground=p["surface"], background=p["surface"], foreground=p["text"], bordercolor=p["line"], lightcolor=p["line"], darkcolor=p["line"], relief="solid", borderwidth=1, padding=(5, 3))
        style.configure("Deck.TCombobox", fieldbackground=p["surface"], background=p["surface"], foreground=p["text"], bordercolor=p["line"], lightcolor=p["line"], darkcolor=p["line"], arrowsize=13, relief="solid", borderwidth=1, padding=(4, 3))
        style.map("Deck.TCombobox", fieldbackground=[("readonly", p["surface"])], background=[("readonly", p["surface"])], foreground=[("readonly", p["text"])])
        style.configure("DeckPrimary.TButton", font=("Segoe UI", 9), padding=(8, 3), foreground="#ffffff", background=p["accent"], bordercolor="#006ab9", lightcolor=p["accent"], darkcolor=p["accent"], relief="solid", borderwidth=1)
        style.map("DeckPrimary.TButton", background=[("active", "#0a84dd"), ("pressed", "#006cbe"), ("disabled", "#c7d7e8")], foreground=[("disabled", "#f4f7fb")])
        style.configure("DeckPrimaryInline.TButton", font=("Segoe UI", 9), padding=(8, 3), foreground="#ffffff", background=p["accent"], bordercolor="#006ab9", lightcolor=p["accent"], darkcolor=p["accent"], relief="solid", borderwidth=1)
        style.map("DeckPrimaryInline.TButton", background=[("active", "#0a84dd"), ("pressed", "#006cbe"), ("disabled", "#c7d7e8")], foreground=[("disabled", "#f4f7fb")])
        style.configure("DeckGhost.TButton", font=("Segoe UI", 9), padding=(8, 3), borderwidth=1, relief="solid", bordercolor=p["line"], lightcolor=p["line"], darkcolor=p["line"], background=p["surface"], foreground=p["text"])
        style.map("DeckGhost.TButton", background=[("active", "#f2f8ff"), ("pressed", "#e6f1ff")], foreground=[("disabled", "#9aa8b7")])
        style.configure(
            "Deck.Vertical.TScrollbar",
            background="#bfd4ea",
            troughcolor="#edf4fb",
            bordercolor="#edf4fb",
            arrowcolor="#6f89a3",
            lightcolor="#edf4fb",
            darkcolor="#edf4fb",
            relief="flat",
            gripcount=0,
            width=11,
        )
        style.configure(
            "Deck.Horizontal.TScrollbar",
            background="#bfd4ea",
            troughcolor="#edf4fb",
            bordercolor="#edf4fb",
            arrowcolor="#6f89a3",
            lightcolor="#edf4fb",
            darkcolor="#edf4fb",
            relief="flat",
            gripcount=0,
            width=11,
        )
        style.layout(
            "Deck.Vertical.TScrollbar",
            [("Vertical.Scrollbar.trough", {"sticky": "ns", "children": [("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]})],
        )
        style.layout(
            "Deck.Horizontal.TScrollbar",
            [("Horizontal.Scrollbar.trough", {"sticky": "we", "children": [("Horizontal.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]})],
        )
        style.configure(
            "Deck.Treeview",
            background=p["surface"],
            fieldbackground=p["surface"],
            foreground=p["text"],
            rowheight=30,
            borderwidth=1,
            relief="solid",
            font=("Segoe UI", 9),
        )
        style.map(
            "Deck.Treeview",
            background=[("selected", p["accent_soft"])],
            foreground=[("selected", p["text"])],
        )
        style.configure(
            "Deck.Treeview.Heading",
            background=p["surface_alt"],
            foreground=p["text"],
            relief="flat",
            borderwidth=1,
            font=("Segoe UI Semibold", 9),
        )
        style.map("Deck.Treeview.Heading", background=[("active", "#f3f0ff")])

    def _center_toplevel(self, win: tk.Toplevel, width: int, height: int) -> None:
        win.update_idletasks()
        screen_w = win.winfo_screenwidth()
        screen_h = win.winfo_screenheight()
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2)
        win.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self) -> None:
        self.main_menu_frame = ttk.Frame(self)
        self.game_screen = ttk.Frame(self)
        self.deck_manager_frame = ttk.Frame(self)

        title = ttk.Label(self.main_menu_frame, text="Holy War", font=("Segoe UI", 26, "bold"))
        title.pack(pady=(90, 24))
        ttk.Button(self.main_menu_frame, text="Gioca", command=self.show_game_screen, width=28).pack(pady=10)
        ttk.Button(
            self.main_menu_frame,
            text="Crea/Modifica deck",
            command=self.show_deck_manager,
            width=28,
        ).pack(pady=10)

        top = ttk.Frame(self.game_screen)
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
        ttk.Button(actions, text="Menu", command=self.show_main_menu).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Nuova Partita", command=self.new_game).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Fine Turno", command=self.end_turn).pack(side="left", padx=4)
        ttk.Button(actions, text="Salva", command=self.save_game).pack(side="left", padx=4)
        ttk.Button(actions, text="Esporta Log", command=self.export_log).pack(side="left", padx=4)
        ttk.Button(actions, text="Catena SI", command=lambda: self.set_chain_enabled(True)).pack(side="left", padx=(12, 4))
        ttk.Button(actions, text="Catena NO", command=lambda: self.set_chain_enabled(False)).pack(side="left", padx=4)
        ttk.Button(actions, text="OK Catena", command=self.chain_ok).pack(side="left", padx=4)
        ttk.Button(actions, text="Deck", command=lambda: self.open_debug_zone("deck")).pack(side="left", padx=(12, 4))
        ttk.Button(actions, text="Cimitero", command=lambda: self.open_debug_zone("graveyard")).pack(side="left", padx=4)
        ttk.Button(actions, text="Scomunicate", command=lambda: self.open_debug_zone("excommunicated")).pack(side="left", padx=4)

        top.columnconfigure(7, weight=1)
        top.columnconfigure(13, weight=1)
        self.p1_rel_combo.bind("<<ComboboxSelected>>", lambda _e: self.update_premade_options())
        self.p2_rel_combo.bind("<<ComboboxSelected>>", lambda _e: self.update_premade_options())
        self.update_premade_options()

        ttk.Label(self.game_screen, textvariable=self.status_var).pack(fill="x", padx=8)

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
        self._build_deck_manager_ui()

    def _build_deck_manager_ui(self) -> None:
        p = self._deck_palette
        self.deck_manager_frame.configure(style="DeckRoot.TFrame")
        top = ttk.Frame(self.deck_manager_frame, style="DeckHero.TFrame")
        top.pack(fill="x", padx=18, pady=(16, 10))
        ttk.Button(top, text="Menu", command=self.show_main_menu, style="DeckGhost.TButton").pack(side="left")
        hero_text = ttk.Frame(top, style="DeckHero.TFrame")
        hero_text.pack(side="left", padx=12)
        ttk.Label(hero_text, text="Deck Builder", style="DeckHeroTitle.TLabel").pack(anchor="w")
        ttk.Label(
            hero_text,
            text="Crea, filtra e rifinisci i deck con regole visibili in tempo reale",
            style="DeckHeroSub.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        body = ttk.Frame(self.deck_manager_frame, style="DeckRoot.TFrame")
        body.pack(fill="both", expand=True, padx=18, pady=(0, 16))
        body.columnconfigure(0, weight=1, minsize=340)
        body.columnconfigure(1, weight=4)
        body.rowconfigure(0, weight=1)

        left = ttk.LabelFrame(body, text="Deck Salvati", style="DeckCard.TLabelframe", padding=(10, 8))
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)
        left_list_wrap = ttk.Frame(left, style="DeckSurface.TFrame")
        left_list_wrap.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        left_list_wrap.columnconfigure(0, weight=1)
        left_list_wrap.rowconfigure(0, weight=1)
        self.deck_listbox = tk.Listbox(left_list_wrap, height=30, width=42)
        self.deck_listbox.grid(row=0, column=0, sticky="nsew")
        self.deck_listbox.configure(
            bg=p["surface"],
            fg=p["text"],
            selectbackground=p["accent_soft"],
            selectforeground=p["text"],
            highlightthickness=0,
            highlightbackground=p["line"],
            relief="flat",
            bd=0,
            activestyle="none",
            font=("Segoe UI", 10),
        )
        self.deck_list_scroll = ttk.Scrollbar(left_list_wrap, orient="vertical", style="Deck.Vertical.TScrollbar", command=self.deck_listbox.yview)
        self.deck_list_scroll.grid(row=0, column=1, sticky="ns")
        self.deck_listbox.configure(yscrollcommand=self.deck_list_scroll.set)
        self.deck_listbox.bind("<<ListboxSelect>>", self._on_deck_manager_select)
        left_btns = ttk.Frame(left, style="DeckSurface.TFrame")
        left_btns.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        ttk.Button(left_btns, text="Nuovo", command=self._deck_manager_new, style="DeckGhost.TButton").pack(side="left", padx=(0, 6))
        ttk.Button(left_btns, text="Elimina", command=self._deck_manager_delete, style="DeckGhost.TButton").pack(side="left")

        right = ttk.Frame(body, style="DeckRoot.TFrame")
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        hdr = ttk.LabelFrame(right, text="Identita Deck", style="DeckCard.TLabelframe", padding=(10, 8))
        hdr.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(hdr, text="Nome Deck", style="DeckTitle.TLabel").grid(row=0, column=0, sticky="w")
        self.deck_name_var = tk.StringVar()
        ttk.Entry(hdr, textvariable=self.deck_name_var, width=36, style="Deck.TEntry").grid(row=0, column=1, sticky="w", padx=6)
        ttk.Label(hdr, text="Religione", style="DeckTitle.TLabel").grid(row=0, column=2, sticky="w", padx=(14, 0))
        self.deck_religion_var = tk.StringVar(value=self.religions[0] if self.religions else "Animismo")
        ttk.Combobox(
            hdr,
            textvariable=self.deck_religion_var,
            values=self.religions,
            width=24,
            state="readonly",
            style="Deck.TCombobox",
        ).grid(row=0, column=3, sticky="w", padx=6)

        pick = ttk.LabelFrame(right, text="Catalogo e Composizione", style="DeckCard.TLabelframe", padding=(8, 8))
        pick.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        pick.columnconfigure(0, weight=1)
        pick.columnconfigure(1, weight=1)
        pick.rowconfigure(2, weight=1)

        self.deck_search_var = tk.StringVar()
        self.deck_search_var.trace_add("write", lambda *_: self._refresh_deck_card_candidates())
        search_row = ttk.Frame(pick, style="DeckSurface.TFrame")
        search_row.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=(8, 4))
        ttk.Label(search_row, text="Cerca", style="DeckTitle.TLabel").pack(side="left")
        ttk.Entry(search_row, textvariable=self.deck_search_var, width=36, style="Deck.TEntry").pack(side="left", padx=6)
        ttk.Label(search_row, text="Espansione", style="DeckTitle.TLabel").pack(side="left", padx=(12, 0))
        self.deck_filter_expansion_var = tk.StringVar(value="Tutte")
        self.deck_filter_expansion_combo = ttk.Combobox(
            search_row,
            textvariable=self.deck_filter_expansion_var,
            values=["Tutte"],
            width=14,
            state="readonly",
            style="Deck.TCombobox",
        )
        self.deck_filter_expansion_combo.pack(side="left", padx=6)
        self.deck_filter_expansion_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_deck_card_candidates())

        filter_row = ttk.Frame(pick, style="DeckSurface.TFrame")
        filter_row.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 4))
        ttk.Label(filter_row, text="Tipo", style="DeckTitle.TLabel").pack(side="left")
        self.deck_filter_type_var = tk.StringVar(value="Tutti")
        self.deck_filter_type_combo = ttk.Combobox(
            filter_row,
            textvariable=self.deck_filter_type_var,
            values=["Tutti", "Santo", "Artefatto", "Edificio", "Benedizione", "Maledizione", "Innata"],
            width=12,
            state="readonly",
            style="Deck.TCombobox",
        )
        self.deck_filter_type_combo.pack(side="left", padx=6)
        self.deck_filter_type_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_deck_card_candidates())

        ttk.Label(filter_row, text="Rarita", style="DeckTitle.TLabel").pack(side="left")
        self.deck_filter_rarity_var = tk.StringVar(value="Tutte")
        self.deck_filter_rarity_combo = ttk.Combobox(
            filter_row,
            textvariable=self.deck_filter_rarity_var,
            values=["Tutte", "1-3", "4-6", "7-9", "10", "Bianca"],
            width=8,
            state="readonly",
            style="Deck.TCombobox",
        )
        self.deck_filter_rarity_combo.pack(side="left", padx=6)
        self.deck_filter_rarity_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_deck_card_candidates())

        ttk.Label(filter_row, text="Croci", style="DeckTitle.TLabel").pack(side="left")
        self.deck_filter_cross_op_var = tk.StringVar(value=">=")
        self.deck_filter_cross_op = ttk.Combobox(
            filter_row,
            textvariable=self.deck_filter_cross_op_var,
            values=["<", "<=", "=", ">=", ">"],
            width=3,
            state="readonly",
            style="Deck.TCombobox",
        )
        self.deck_filter_cross_op.pack(side="left", padx=(4, 2))
        self.deck_filter_cross_op.bind("<<ComboboxSelected>>", lambda _e: self._refresh_deck_card_candidates())
        self.deck_filter_cross_val_var = tk.StringVar(value="")
        self.deck_filter_cross_val = ttk.Entry(filter_row, textvariable=self.deck_filter_cross_val_var, width=4, style="Deck.TEntry")
        self.deck_filter_cross_val.pack(side="left", padx=(0, 8))
        self.deck_filter_cross_val_var.trace_add("write", lambda *_: self._refresh_deck_card_candidates())

        ttk.Label(filter_row, text="Forza", style="DeckTitle.TLabel").pack(side="left")
        self.deck_filter_strength_op_var = tk.StringVar(value=">=")
        self.deck_filter_strength_op = ttk.Combobox(
            filter_row,
            textvariable=self.deck_filter_strength_op_var,
            values=["<", "<=", "=", ">=", ">"],
            width=3,
            state="readonly",
            style="Deck.TCombobox",
        )
        self.deck_filter_strength_op.pack(side="left", padx=(4, 2))
        self.deck_filter_strength_op.bind("<<ComboboxSelected>>", lambda _e: self._refresh_deck_card_candidates())
        self.deck_filter_strength_val_var = tk.StringVar(value="")
        self.deck_filter_strength_val = ttk.Entry(filter_row, textvariable=self.deck_filter_strength_val_var, width=4, style="Deck.TEntry")
        self.deck_filter_strength_val.pack(side="left", padx=(0, 8))
        self.deck_filter_strength_val_var.trace_add("write", lambda *_: self._refresh_deck_card_candidates())

        ttk.Label(filter_row, text="Fede", style="DeckTitle.TLabel").pack(side="left")
        self.deck_filter_faith_op_var = tk.StringVar(value=">=")
        self.deck_filter_faith_op = ttk.Combobox(
            filter_row,
            textvariable=self.deck_filter_faith_op_var,
            values=["<", "<=", "=", ">=", ">"],
            width=3,
            state="readonly",
            style="Deck.TCombobox",
        )
        self.deck_filter_faith_op.pack(side="left", padx=(4, 2))
        self.deck_filter_faith_op.bind("<<ComboboxSelected>>", lambda _e: self._refresh_deck_card_candidates())
        self.deck_filter_faith_val_var = tk.StringVar(value="")
        self.deck_filter_faith_val = ttk.Entry(filter_row, textvariable=self.deck_filter_faith_val_var, width=4, style="Deck.TEntry")
        self.deck_filter_faith_val.pack(side="left", padx=(0, 8))
        self.deck_filter_faith_val_var.trace_add("write", lambda *_: self._refresh_deck_card_candidates())

        ttk.Label(filter_row, text="Ordina", style="DeckTitle.TLabel").pack(side="left")
        self.deck_sort_var = tk.StringVar(value="Nome A-Z")
        self.deck_sort_combo = ttk.Combobox(
            filter_row,
            textvariable=self.deck_sort_var,
            values=[
                "Nome A-Z",
                "Croci ↑",
                "Croci ↓",
                "Forza ↑",
                "Forza ↓",
                "Fede ↑",
                "Fede ↓",
                "Tipo",
            ],
            width=11,
            state="readonly",
            style="Deck.TCombobox",
        )
        self.deck_sort_combo.pack(side="left", padx=6)
        self.deck_sort_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_deck_card_candidates())

        cand_wrap = ttk.Frame(pick)
        cand_wrap.grid(row=2, column=0, sticky="nsew", padx=(8, 4), pady=(0, 8))
        cand_wrap.columnconfigure(0, weight=1)
        cand_wrap.rowconfigure(0, weight=1)
        self.deck_candidates = ttk.Treeview(
            cand_wrap,
            columns=("nome", "tipo", "croci", "forza", "fede", "espansione", "max", "nel_deck"),
            show="headings",
            height=16,
            style="Deck.Treeview",
        )
        self.deck_candidates.grid(row=0, column=0, sticky="nsew")
        self.deck_candidates_y = ttk.Scrollbar(cand_wrap, orient="vertical", style="Deck.Vertical.TScrollbar", command=self.deck_candidates.yview)
        self.deck_candidates_y.grid(row=0, column=1, sticky="ns")
        self.deck_candidates.configure(yscrollcommand=self.deck_candidates_y.set)
        self.deck_candidates.heading("nome", text="Nome", command=lambda: self._sort_deck_candidates_by("nome"))
        self.deck_candidates.heading("tipo", text="Tipo", command=lambda: self._sort_deck_candidates_by("tipo"))
        self.deck_candidates.heading("croci", text="Croci", command=lambda: self._sort_deck_candidates_by("croci"))
        self.deck_candidates.heading("forza", text="Forza", command=lambda: self._sort_deck_candidates_by("forza"))
        self.deck_candidates.heading("fede", text="Fede", command=lambda: self._sort_deck_candidates_by("fede"))
        self.deck_candidates.heading("espansione", text="Exp", command=lambda: self._sort_deck_candidates_by("espansione"))
        self.deck_candidates.heading("max", text="Max", command=lambda: self._sort_deck_candidates_by("max"))
        self.deck_candidates.heading("nel_deck", text="Deck", command=lambda: self._sort_deck_candidates_by("nel_deck"))
        self.deck_candidates.column("nome", width=220, anchor="w")
        self.deck_candidates.column("tipo", width=90, anchor="w")
        self.deck_candidates.column("croci", width=50, anchor="center")
        self.deck_candidates.column("forza", width=50, anchor="center")
        self.deck_candidates.column("fede", width=50, anchor="center")
        self.deck_candidates.column("espansione", width=70, anchor="center")
        self.deck_candidates.column("max", width=46, anchor="center")
        self.deck_candidates.column("nel_deck", width=52, anchor="center")
        self.deck_candidates.bind("<<TreeviewSelect>>", self._on_deck_candidates_select)

        cur_wrap = ttk.Frame(pick)
        cur_wrap.grid(row=2, column=1, sticky="nsew", padx=(4, 8), pady=(0, 8))
        cur_wrap.columnconfigure(0, weight=1)
        cur_wrap.rowconfigure(0, weight=1)
        self.deck_current = ttk.Treeview(
            cur_wrap,
            columns=("nome", "tipo", "croci", "forza", "fede", "espansione", "qta"),
            show="headings",
            height=16,
            style="Deck.Treeview",
        )
        self.deck_current.grid(row=0, column=0, sticky="nsew")
        self.deck_current_y = ttk.Scrollbar(cur_wrap, orient="vertical", style="Deck.Vertical.TScrollbar", command=self.deck_current.yview)
        self.deck_current_y.grid(row=0, column=1, sticky="ns")
        self.deck_current.configure(yscrollcommand=self.deck_current_y.set)
        self.deck_current.heading("nome", text="Nome", command=lambda: self._sort_deck_current_by("nome"))
        self.deck_current.heading("tipo", text="Tipo", command=lambda: self._sort_deck_current_by("tipo"))
        self.deck_current.heading("croci", text="Croci", command=lambda: self._sort_deck_current_by("croci"))
        self.deck_current.heading("forza", text="Forza", command=lambda: self._sort_deck_current_by("forza"))
        self.deck_current.heading("fede", text="Fede", command=lambda: self._sort_deck_current_by("fede"))
        self.deck_current.heading("espansione", text="Exp", command=lambda: self._sort_deck_current_by("espansione"))
        self.deck_current.heading("qta", text="Qta", command=lambda: self._sort_deck_current_by("qta"))
        self.deck_current.column("nome", width=220, anchor="w")
        self.deck_current.column("tipo", width=90, anchor="w")
        self.deck_current.column("croci", width=50, anchor="center")
        self.deck_current.column("forza", width=50, anchor="center")
        self.deck_current.column("fede", width=50, anchor="center")
        self.deck_current.column("espansione", width=70, anchor="center")
        self.deck_current.column("qta", width=52, anchor="center")
        self.deck_current.bind("<<TreeviewSelect>>", self._on_deck_current_select)

        ctrls = ttk.Frame(right, style="DeckRoot.TFrame")
        ctrls.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        self.deck_qty_var = tk.StringVar(value="1")
        ttk.Label(ctrls, text="Quantita", style="DeckTitle.TLabel").pack(side="left")
        ttk.Entry(ctrls, textvariable=self.deck_qty_var, width=5, style="Deck.TEntry").pack(side="left", padx=6)
        ttk.Button(ctrls, text="Aggiungi", command=self._deck_add_selected_card, style="DeckPrimaryInline.TButton").pack(side="left", padx=(0, 10))
        ttk.Button(ctrls, text="+1", command=lambda: self._deck_adjust_selected_card(1), style="DeckGhost.TButton").pack(side="left", padx=(0, 6))
        ttk.Button(ctrls, text="-1", command=lambda: self._deck_adjust_selected_card(-1), style="DeckGhost.TButton").pack(side="left", padx=(0, 6))
        ttk.Button(ctrls, text="Rimuovi", command=self._deck_remove_selected_card, style="DeckGhost.TButton").pack(side="left")
        ttk.Button(
            ctrls,
            text="Filtro Colonne (Carte)",
            command=lambda: self._open_excel_like_filter_dialog("candidates"),
            style="DeckGhost.TButton",
        ).pack(side="left", padx=(12, 6))
        ttk.Button(
            ctrls,
            text="Filtro Colonne (Deck)",
            command=lambda: self._open_excel_like_filter_dialog("current"),
            style="DeckGhost.TButton",
        ).pack(side="left", padx=(0, 6))

        rules_box = ttk.LabelFrame(right, text="Regole e Validazione", style="DeckCard.TLabelframe", padding=(8, 6))
        rules_box.grid(row=3, column=0, sticky="ew")
        rules_box.columnconfigure(0, weight=1)
        self.deck_rules_label = ttk.Label(
            rules_box,
            text="",
            justify="left",
            anchor="w",
            wraplength=900,
            style="DeckMuted.TLabel",
        )
        self.deck_rules_label.grid(row=0, column=0, sticky="ew", padx=8, pady=8)

        bottom = ttk.Frame(right, style="DeckRoot.TFrame")
        bottom.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(bottom, text="Salva Deck", command=self._deck_manager_save, style="DeckPrimary.TButton").pack(side="left")
        ttk.Button(bottom, text="Pulisci filtri", command=self._reset_deck_filters, style="DeckGhost.TButton").pack(side="left", padx=(8, 0))

        details = ttk.LabelFrame(right, text="Dettaglio Effetto Carta", style="DeckCard.TLabelframe", padding=(8, 6))
        details.grid(row=5, column=0, sticky="nsew", pady=(8, 0))
        details.columnconfigure(0, weight=1)
        details.rowconfigure(0, weight=1)
        self.deck_effect_text = tk.Text(details, wrap="word", height=6)
        self.deck_effect_text.grid(row=0, column=0, sticky="nsew")
        self.deck_effect_scroll = ttk.Scrollbar(details, orient="vertical", style="Deck.Vertical.TScrollbar", command=self.deck_effect_text.yview)
        self.deck_effect_scroll.grid(row=0, column=1, sticky="ns")
        self.deck_effect_text.configure(
            yscrollcommand=self.deck_effect_scroll.set,
            state="disabled",
            relief="flat",
            bd=0,
            bg=p["surface"],
            fg=p["text"],
            insertbackground=p["text"],
            padx=8,
            pady=8,
        )

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

    def _norm(self, text: str) -> str:
        value = (
            str(text or "")
            .replace("â€™", "'")
            .replace("`", "'")
            .replace("Ã¸", "o")
            .replace("Ã˜", "O")
            .replace("Ã°", "d")
            .replace("Ã", "D")
        )
        return _norm(value)

    def _cross_value(self, crosses: str) -> int | None:
        txt = str(crosses or "").strip().lower()
        if txt in {"white", "croce bianca"}:
            return 11
        try:
            return int(float(txt))
        except Exception:
            return None

    def _max_copies_for_crosses(self, crosses: str) -> int:
        value = self._cross_value(crosses)
        if value is None:
            return 1
        if 1 <= value <= 3:
            return 5
        if 4 <= value <= 6:
            return 3
        return 1

    def _premades_payload(self) -> dict:
        if not self.premades_path.exists():
            return {"decks": []}
        try:
            raw = json.loads(self.premades_path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                return {"decks": []}
            decks = raw.get("decks", [])
            if not isinstance(decks, list):
                decks = []
            return {
                "decks": [d for d in decks if isinstance(d, dict)],
            }
        except Exception:
            return {"decks": []}

    def _save_premades_payload(self, payload: dict) -> None:
        self.premades_path.parent.mkdir(parents=True, exist_ok=True)
        self.premades_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_premades_into_runtime(self) -> None:
        if self.premades_path.exists():
            register_premades_from_json(self.premades_path)

    def _deck_name_to_def(self) -> dict[str, object]:
        return {self._norm(c.name): c for c in self.cards}

    def _deck_rules_report(self) -> tuple[list[str], list[str], int, dict[str, int]]:
        hard: list[str] = []
        soft: list[str] = []
        by_name = self._deck_name_to_def()
        total = sum(max(0, int(q)) for q in self._deck_editor_cards.values())
        stats = {
            "band_13": 0,
            "band_46": 0,
            "band_79": 0,
            "band_10": 0,
            "band_white": 0,
            "innata": 0,
        }
        if total < 45:
            hard.append(f"Carte nel reliquiario insufficienti: {total}/45 (minimo 45).")

        total_79 = 0
        total_10 = 0
        total_white = 0
        for name, qty in sorted(self._deck_editor_cards.items()):
            if qty <= 0:
                continue
            card = by_name.get(name)
            if card is None:
                hard.append(f"Carta non trovata nel catalogo: {name}")
                continue
            crosses = str(getattr(card, "crosses", ""))
            max_copy = self._max_copies_for_crosses(crosses)
            if qty > max_copy:
                hard.append(f"{getattr(card, 'name', name)}: {qty} copie (max {max_copy}).")
            ctype = str(getattr(card, "card_type", "")).strip().lower()
            if ctype == "innata":
                soft.append(f"{getattr(card, 'name', name)} e Innata: usarla solo in deck tematici.")
                stats["innata"] += qty
            cval = self._cross_value(crosses)
            if cval is None:
                continue
            if 1 <= cval <= 3:
                stats["band_13"] += qty
            elif 4 <= cval <= 6:
                stats["band_46"] += qty
            elif 7 <= cval <= 9:
                total_79 += qty
                stats["band_79"] += qty
            elif cval == 10:
                total_10 += qty
                stats["band_10"] += qty
            elif cval >= 11:
                total_white += qty
                stats["band_white"] += qty

        if total_79 > 10:
            hard.append(f"Carte 7-9 Croci: {total_79}/10 (massimo 10).")
        if total_10 > 3:
            hard.append(f"Carte 10 Croci: {total_10}/3 (massimo 3).")
        if total_white > 1:
            hard.append(f"Carte Croce Bianca: {total_white}/1 (massimo 1).")
        return hard, soft, total, stats

    def _render_deck_rules(self) -> None:
        hard, soft, total, stats = self._deck_rules_report()
        lines = [
            f"Totale carte reliquiario: {total}",
            "",
            "Limitazioni deck:",
            f"1–3 Croci: {stats['band_13']} carte totali, massimo 5 copie per carta",
            f"4–6 Croci: {stats['band_46']} carte totali, massimo 3 copie per carta",
            f"7–9 Croci: {stats['band_79']}/10 carte totali, 1 copia per carta",
            f"10 Croci: {stats['band_10']}/3 carte totali, 1 copia per carta",
            f"Croce Bianca: {stats['band_white']}/1 carta, 1 copia per carta",
            f"Carta innata: {stats['innata']} nel deck (utilizzabili solo in reliquiario a tematica particolare)",
            "",
        ]
        if hard:
            lines.append("Errori regolamento:")
            lines.extend(f"- {m}" for m in hard)
        else:
            lines.append("Regolamento: OK")
        if soft:
            lines.append("Note:")
            lines.extend(f"- {m}" for m in soft)
        self.deck_rules_label.configure(text="\n".join(lines))

    def _deck_manager_reload_user_decks(self) -> None:
        self._deck_entries = runtime_premade_decks()
        self.deck_listbox.delete(0, tk.END)
        for deck in self._deck_entries:
            label = f"{deck.get('name', 'Deck')} [{deck.get('religion', '-')}]"
            self.deck_listbox.insert(tk.END, label)
        self._deck_manager_new()
        self._refresh_deck_card_candidates()

    def _deck_manager_new(self) -> None:
        self._deck_editor_selected_id = None
        self._deck_editor_cards = {}
        self.deck_name_var.set("")
        if self.religions:
            self.deck_religion_var.set(self.religions[0])
        self.deck_current.delete(*self.deck_current.get_children(""))
        self.deck_listbox.selection_clear(0, tk.END)
        self._render_deck_rules()

    def _deck_manager_delete(self) -> None:
        sel = self.deck_listbox.curselection()
        if not sel:
            return
        idx = int(sel[0])
        if idx < 0 or idx >= len(self._deck_entries):
            return
        deck = self._deck_entries[idx]
        deck_id = str(deck.get("id", "")).strip()
        if not deck_id:
            return
        if not messagebox.askyesno("Elimina deck", f"Confermi eliminazione di '{deck.get('name', 'Deck')}'?"):
            return
        payload = self._premades_payload()
        payload["decks"] = [d for d in payload.get("decks", []) if str(d.get("id", "")) != deck_id]
        self._save_premades_payload(payload)
        reset_runtime_premades()
        self._load_premades_into_runtime()
        self.update_premade_options()
        self._deck_manager_reload_user_decks()

    def _on_deck_manager_select(self, _event=None) -> None:
        sel = self.deck_listbox.curselection()
        if not sel:
            return
        idx = int(sel[0])
        if idx < 0 or idx >= len(self._deck_entries):
            return
        deck = self._deck_entries[idx]
        self._deck_editor_selected_id = str(deck.get("id", "")).strip() or None
        self.deck_name_var.set(str(deck.get("name", "")))
        rel = str(deck.get("religion", "")).strip()
        if rel:
            self.deck_religion_var.set(rel)
        cards = {}
        for c in deck.get("cards", []):
            name = ""
            qty = 0
            if isinstance(c, dict):
                name = self._norm(str(c.get("name", "")))
                qty = int(c.get("qty", 0) or 0)
            elif isinstance(c, (tuple, list)) and len(c) >= 2:
                name = self._norm(str(c[0]))
                qty = int(c[1] or 0)
            if name and qty > 0:
                cards[name] = cards.get(name, 0) + qty
        self._deck_editor_cards = cards
        self._sync_deck_filter_expansions()
        self._refresh_deck_current_list()

    def _rarity_bucket(self, crosses: str) -> str:
        val = self._cross_value(crosses)
        if val is None:
            return "?"
        if 1 <= val <= 3:
            return "1-3"
        if 4 <= val <= 6:
            return "4-6"
        if 7 <= val <= 9:
            return "7-9"
        if val == 10:
            return "10"
        return "Bianca"

    def _sync_deck_filter_expansions(self) -> None:
        values = ["Tutte"]
        seen = set(values)
        for c in self.cards:
            exp = str(getattr(c, "expansion", "") or "").strip()
            if exp and exp not in seen:
                values.append(exp)
                seen.add(exp)
        self.deck_filter_expansion_combo.configure(values=values)
        if self.deck_filter_expansion_var.get() not in seen:
            self.deck_filter_expansion_var.set("Tutte")

    def _parse_filter_number(self, value: str) -> int | None:
        raw = str(value or "").strip()
        if not raw:
            return None
        try:
            return int(raw)
        except Exception:
            return None

    def _compare_number(self, current: int, operator: str, wanted: int) -> bool:
        op = str(operator or "=").strip()
        if op == "<":
            return current < wanted
        if op == "<=":
            return current <= wanted
        if op == ">":
            return current > wanted
        if op == ">=":
            return current >= wanted
        return current == wanted

    def _reset_deck_filters(self) -> None:
        self.deck_search_var.set("")
        self.deck_filter_expansion_var.set("Tutte")
        self.deck_filter_type_var.set("Tutti")
        self.deck_filter_rarity_var.set("Tutte")
        self.deck_filter_cross_op_var.set(">=")
        self.deck_filter_cross_val_var.set("")
        self.deck_filter_strength_op_var.set(">=")
        self.deck_filter_strength_val_var.set("")
        self.deck_filter_faith_op_var.set(">=")
        self.deck_filter_faith_val_var.set("")
        self.deck_sort_var.set("Nome A-Z")
        self._deck_candidates_sort_col = "nome"
        self._deck_candidates_sort_asc = True
        self._deck_candidates_value_filters = {}
        self._deck_current_value_filters = {}
        self._refresh_deck_card_candidates()

    def _open_excel_like_filter_dialog(self, table: str) -> None:
        table_key = str(table or "").strip().lower()
        if table_key not in {"candidates", "current"}:
            return

        if table_key == "candidates":
            columns = [
                ("Nome", "nome"),
                ("Tipo", "tipo"),
                ("Croci", "croci"),
                ("Forza", "forza"),
                ("Fede", "fede"),
                ("Exp", "espansione"),
                ("Max", "max"),
                ("Deck", "nel_deck"),
            ]
            rows = list(self._deck_candidates_rows_cache)
            active_filters = {k: set(v) for k, v in self._deck_candidates_value_filters.items()}
            sort_col = self._deck_candidates_sort_col
            sort_asc = self._deck_candidates_sort_asc
            title = "Filtro Colonne - Carte"
        else:
            columns = [
                ("Nome", "nome"),
                ("Tipo", "tipo"),
                ("Croci", "croci"),
                ("Forza", "forza"),
                ("Fede", "fede"),
                ("Exp", "espansione"),
                ("Qta", "qta"),
            ]
            rows = list(self._deck_current_rows_cache)
            active_filters = {k: set(v) for k, v in self._deck_current_value_filters.items()}
            sort_col = self._deck_current_sort_col
            sort_asc = self._deck_current_sort_asc
            title = "Filtro Colonne - Deck"

        if not rows:
            messagebox.showinfo("Filtro", "Nessun dato disponibile da filtrare.")
            return

        win = tk.Toplevel(self)
        win.title(title)
        win.transient(self)
        win.grab_set()
        self._center_toplevel(win, 460, 560)

        col_var = tk.StringVar(value=columns[0][0])
        search_var = tk.StringVar(value="")
        sort_dir_var = tk.StringVar(value="asc" if sort_asc else "desc")
        col_label_to_key = {label: key for label, key in columns}

        top = ttk.Frame(win)
        top.pack(fill="x", padx=10, pady=10)
        ttk.Label(top, text="Colonna").pack(side="left")
        col_combo = ttk.Combobox(
            top,
            textvariable=col_var,
            values=[label for label, _ in columns],
            width=16,
            state="readonly",
        )
        col_combo.pack(side="left", padx=6)
        ttk.Button(top, text="A→Z", command=lambda: sort_dir_var.set("asc")).pack(side="left", padx=(10, 4))
        ttk.Button(top, text="Z→A", command=lambda: sort_dir_var.set("desc")).pack(side="left", padx=4)

        search_row = ttk.Frame(win)
        search_row.pack(fill="x", padx=10, pady=(0, 6))
        ttk.Label(search_row, text="Cerca valore").pack(side="left")
        ttk.Entry(search_row, textvariable=search_var, width=28).pack(side="left", padx=6)

        list_wrap = ttk.Frame(win)
        list_wrap.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        list_wrap.columnconfigure(0, weight=1)
        list_wrap.rowconfigure(0, weight=1)
        values_list = tk.Listbox(list_wrap, selectmode="extended")
        values_list.grid(row=0, column=0, sticky="nsew")
        values_scroll = ttk.Scrollbar(list_wrap, orient="vertical", command=values_list.yview)
        values_scroll.grid(row=0, column=1, sticky="ns")
        values_list.configure(yscrollcommand=values_scroll.set)

        actions = ttk.Frame(win)
        actions.pack(fill="x", padx=10, pady=(0, 8))
        ttk.Button(actions, text="Seleziona tutto", command=lambda: values_list.select_set(0, tk.END)).pack(side="left")
        ttk.Button(actions, text="Deseleziona", command=lambda: values_list.select_clear(0, tk.END)).pack(side="left", padx=6)

        def current_col_key() -> str:
            return col_label_to_key.get(str(col_var.get()), columns[0][1])

        def get_unique_values(col_key: str) -> list[str]:
            vals = {str(r.get(col_key, "")) for r in rows}
            out = sorted(vals, key=lambda v: self._norm(v))
            term = self._norm(search_var.get())
            if term:
                out = [v for v in out if term in self._norm(v)]
            return out

        def refresh_values() -> None:
            col_key = current_col_key()
            values = get_unique_values(col_key)
            values_list.delete(0, tk.END)
            for v in values:
                values_list.insert(tk.END, v)
            selected = active_filters.get(col_key, set())
            if not selected:
                values_list.select_set(0, tk.END)
                return
            for i, val in enumerate(values):
                if val in selected:
                    values_list.select_set(i)

        def capture_current_selection() -> None:
            col_key = current_col_key()
            all_vals = get_unique_values(col_key)
            idxs = values_list.curselection()
            selected_vals = {all_vals[i] for i in idxs if 0 <= i < len(all_vals)}
            if selected_vals and len(selected_vals) < len(all_vals):
                active_filters[col_key] = selected_vals
            else:
                active_filters.pop(col_key, None)

        def on_column_change(*_args) -> None:
            refresh_values()

        def on_search_change(*_args) -> None:
            refresh_values()

        col_var.trace_add("write", on_column_change)
        search_var.trace_add("write", on_search_change)
        refresh_values()

        result = {"ok": False}

        def apply_and_close() -> None:
            capture_current_selection()
            chosen_col = current_col_key()
            if table_key == "candidates":
                self._deck_candidates_value_filters = active_filters
                self._deck_candidates_sort_col = chosen_col
                self._deck_candidates_sort_asc = sort_dir_var.get() != "desc"
                self._refresh_deck_card_candidates()
            else:
                self._deck_current_value_filters = active_filters
                self._deck_current_sort_col = chosen_col
                self._deck_current_sort_asc = sort_dir_var.get() != "desc"
                self._refresh_deck_current_list()
            result["ok"] = True
            win.destroy()

        def cancel() -> None:
            win.destroy()

        bottom = ttk.Frame(win)
        bottom.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(bottom, text="OK", command=apply_and_close).pack(side="right")
        ttk.Button(bottom, text="Annulla", command=cancel).pack(side="right", padx=6)

    def _show_deck_effect_from_key(self, key: str | None) -> None:
        if not key:
            return
        by_name = self._deck_name_to_def()
        card = by_name.get(str(key))
        if card is None:
            return
        name = str(getattr(card, "name", key))
        effect = str(getattr(card, "effect_text", "") or "").strip() or "Nessun effetto testuale disponibile."
        text = f"{name}\n\n{effect}"
        self.deck_effect_text.configure(state="normal")
        self.deck_effect_text.delete("1.0", tk.END)
        self.deck_effect_text.insert("1.0", text)
        self.deck_effect_text.configure(state="disabled")

    def _on_deck_candidates_select(self, _event=None) -> None:
        selected = self.deck_candidates.selection()
        if not selected:
            return
        key = self._deck_candidate_iid_to_key.get(str(selected[0]))
        self._show_deck_effect_from_key(key)

    def _apply_treeview_zebra(self, tree: ttk.Treeview) -> None:
        tree.tag_configure("even", background=self._deck_palette["surface"])
        tree.tag_configure("odd", background="#fdfcff")
        for pos, item_id in enumerate(tree.get_children("")):
            tree.item(item_id, tags=("even" if (pos % 2 == 0) else "odd",))

    def _refresh_deck_card_candidates(self) -> None:
        txt = self._norm(self.deck_search_var.get())
        ctype_filter = str(self.deck_filter_type_var.get() or "Tutti").strip().lower()
        rarity_filter = str(self.deck_filter_rarity_var.get() or "Tutte").strip()
        exp_filter = str(self.deck_filter_expansion_var.get() or "Tutte").strip()
        sort_mode = str(self.deck_sort_var.get() or "Nome A-Z").strip()
        cross_filter_value = self._parse_filter_number(self.deck_filter_cross_val_var.get())
        strength_filter_value = self._parse_filter_number(self.deck_filter_strength_val_var.get())
        faith_filter_value = self._parse_filter_number(self.deck_filter_faith_val_var.get())
        self.deck_candidates.delete(*self.deck_candidates.get_children(""))
        self._deck_candidate_iid_to_key: dict[str, str] = {}
        rows: list[tuple] = []
        # cards.json may contain duplicated rows for the same card name.
        # For the picker we show each logical card only once.
        unique_cards: dict[str, object] = {}
        for card in self.cards:
            key = self._norm(getattr(card, "name", ""))
            if not key or key in unique_cards:
                continue
            unique_cards[key] = card
        for card in unique_cards.values():
            ctype = str(card.card_type).strip().lower()
            if ctype == "token":
                continue
            if ctype_filter != "tutti" and ctype != ctype_filter:
                continue
            if exp_filter != "Tutte" and str(card.expansion) != exp_filter:
                continue
            key = self._norm(card.name)
            if txt and txt not in self._norm(card.name):
                continue
            if rarity_filter != "Tutte" and self._rarity_bucket(str(card.crosses)) != rarity_filter:
                continue
            strength = int(card.strength or 0) if card.strength is not None else 0
            faith = int(card.faith or 0) if card.faith is not None else 0
            crosses_val = self._cross_value(str(card.crosses))
            if cross_filter_value is not None:
                if crosses_val is None or not self._compare_number(crosses_val, self.deck_filter_cross_op_var.get(), cross_filter_value):
                    continue
            if strength_filter_value is not None and not self._compare_number(strength, self.deck_filter_strength_op_var.get(), strength_filter_value):
                continue
            if faith_filter_value is not None and not self._compare_number(faith, self.deck_filter_faith_op_var.get(), faith_filter_value):
                continue
            crosses_sort = crosses_val if crosses_val is not None else 99
            rows.append((key, card, ctype, crosses_sort, strength, faith))

        # Sort mode from combobox is still supported; click-on-header overrides it.
        if self._deck_candidates_sort_col == "nome" and sort_mode != "Nome A-Z":
            if sort_mode == "Croci ↑":
                self._deck_candidates_sort_col, self._deck_candidates_sort_asc = "croci", True
            elif sort_mode == "Croci ↓":
                self._deck_candidates_sort_col, self._deck_candidates_sort_asc = "croci", False
            elif sort_mode == "Forza ↑":
                self._deck_candidates_sort_col, self._deck_candidates_sort_asc = "forza", True
            elif sort_mode == "Forza ↓":
                self._deck_candidates_sort_col, self._deck_candidates_sort_asc = "forza", False
            elif sort_mode == "Fede ↑":
                self._deck_candidates_sort_col, self._deck_candidates_sort_asc = "fede", True
            elif sort_mode == "Fede ↓":
                self._deck_candidates_sort_col, self._deck_candidates_sort_asc = "fede", False
            elif sort_mode == "Tipo":
                self._deck_candidates_sort_col, self._deck_candidates_sort_asc = "tipo", True

        if self._deck_candidates_sort_col == "croci":
            rows.sort(key=lambda r: (r[3], self._norm(r[1].name)), reverse=not self._deck_candidates_sort_asc)
        elif self._deck_candidates_sort_col == "forza":
            rows.sort(key=lambda r: (r[4], self._norm(r[1].name)), reverse=not self._deck_candidates_sort_asc)
        elif self._deck_candidates_sort_col == "fede":
            rows.sort(key=lambda r: (r[5], self._norm(r[1].name)), reverse=not self._deck_candidates_sort_asc)
        elif self._deck_candidates_sort_col == "tipo":
            rows.sort(key=lambda r: (r[2], self._norm(r[1].name)), reverse=not self._deck_candidates_sort_asc)
        elif self._deck_candidates_sort_col == "espansione":
            rows.sort(key=lambda r: (str(r[1].expansion), self._norm(r[1].name)), reverse=not self._deck_candidates_sort_asc)
        elif self._deck_candidates_sort_col == "max":
            rows.sort(
                key=lambda r: (
                    self._max_copies_for_crosses(str(r[1].crosses)),
                    self._norm(r[1].name),
                ),
                reverse=not self._deck_candidates_sort_asc,
            )
        elif self._deck_candidates_sort_col == "nel_deck":
            rows.sort(
                key=lambda r: (
                    int(self._deck_editor_cards.get(r[0], 0)),
                    self._norm(r[1].name),
                ),
                reverse=not self._deck_candidates_sort_asc,
            )
        else:
            rows.sort(key=lambda r: self._norm(r[1].name), reverse=not self._deck_candidates_sort_asc)

        # Cache rows for excel-like filter dialog and apply per-column value filters.
        self._deck_candidates_rows_cache = []
        for key, card, ctype, _cross_sort, strength, faith in rows:
            self._deck_candidates_rows_cache.append(
                {
                    "key": key,
                    "nome": str(card.name),
                    "tipo": str(card.card_type),
                    "croci": str(card.crosses),
                    "forza": str(strength),
                    "fede": str(faith),
                    "espansione": str(card.expansion),
                    "max": str(self._max_copies_for_crosses(str(card.crosses))),
                    "nel_deck": str(int(self._deck_editor_cards.get(key, 0))),
                    "card": card,
                    "ctype": ctype,
                    "strength": strength,
                    "faith": faith,
                }
            )

        filtered_rows = []
        for row in self._deck_candidates_rows_cache:
            keep = True
            for col, accepted in self._deck_candidates_value_filters.items():
                if accepted and str(row.get(col, "")) not in accepted:
                    keep = False
                    break
            if keep:
                filtered_rows.append(row)

        allowed_keys = {r["key"] for r in filtered_rows}
        visible_idx = 0
        for idx, (key, card, _ctype, _cross_sort, strength, faith) in enumerate(rows):
            if key not in allowed_keys:
                continue
            qty_now = int(self._deck_editor_cards.get(key, 0))
            max_copy = self._max_copies_for_crosses(str(card.crosses))
            iid = f"cand_{idx}"
            self._deck_candidate_iid_to_key[iid] = key
            self.deck_candidates.insert(
                "",
                "end",
                iid=iid,
                tags=("even" if (visible_idx % 2 == 0) else "odd",),
                values=(
                    str(card.name),
                    str(card.card_type),
                    str(card.crosses),
                    str(strength),
                    str(faith),
                    str(card.expansion),
                    str(max_copy),
                    str(qty_now),
                ),
            )
            visible_idx += 1
        self._apply_treeview_zebra(self.deck_candidates)

    def _refresh_deck_current_list(self) -> None:
        by_name = self._deck_name_to_def()
        self.deck_current.delete(*self.deck_current.get_children(""))
        self._deck_current_iid_to_key: dict[str, str] = {}
        self._deck_current_rows_cache = []
        for idx, key in enumerate(sorted(self._deck_editor_cards.keys())):
            qty = int(self._deck_editor_cards.get(key, 0))
            if qty <= 0:
                continue
            card = by_name.get(key)
            name = str(getattr(card, "name", key))
            ctype = str(getattr(card, "card_type", "?"))
            crosses = str(getattr(card, "crosses", "?"))
            strength = int(getattr(card, "strength", 0) or 0)
            faith = int(getattr(card, "faith", 0) or 0)
            expansion = str(getattr(card, "expansion", "?"))
            iid = f"cur_{idx}"
            self._deck_current_iid_to_key[iid] = key
            self._deck_current_rows_cache.append(
                {
                    "key": key,
                    "nome": name,
                    "tipo": ctype,
                    "croci": crosses,
                    "forza": str(strength),
                    "fede": str(faith),
                    "espansione": expansion,
                    "qta": str(qty),
                }
            )
            self.deck_current.insert(
                "",
                "end",
                iid=iid,
                values=(name, ctype, crosses, str(strength), str(faith), expansion, str(qty)),
            )
        # Reorder current deck rows according to header sort.
        children = list(self.deck_current.get_children(""))
        def _cur_sort_value(item_id: str):
            vals = list(self.deck_current.item(item_id, "values"))
            col = self._deck_current_sort_col
            mapper = {
                "nome": 0,
                "tipo": 1,
                "croci": 2,
                "forza": 3,
                "fede": 4,
                "espansione": 5,
                "qta": 6,
            }
            idx = mapper.get(col, 0)
            val = vals[idx] if idx < len(vals) else ""
            if col in {"croci", "forza", "fede", "qta"}:
                try:
                    if col == "croci":
                        return self._cross_value(str(val)) or 99
                    return int(str(val))
                except Exception:
                    return 0
            return self._norm(str(val))
        children.sort(key=_cur_sort_value, reverse=not self._deck_current_sort_asc)
        for pos, item_id in enumerate(children):
            self.deck_current.move(item_id, "", pos)

        # Apply value filters for current deck table.
        if self._deck_current_value_filters:
            for item_id in list(self.deck_current.get_children("")):
                vals = list(self.deck_current.item(item_id, "values"))
                row = {
                    "nome": vals[0] if len(vals) > 0 else "",
                    "tipo": vals[1] if len(vals) > 1 else "",
                    "croci": vals[2] if len(vals) > 2 else "",
                    "forza": vals[3] if len(vals) > 3 else "",
                    "fede": vals[4] if len(vals) > 4 else "",
                    "espansione": vals[5] if len(vals) > 5 else "",
                    "qta": vals[6] if len(vals) > 6 else "",
                }
                keep = True
                for col, accepted in self._deck_current_value_filters.items():
                    if accepted and str(row.get(col, "")) not in accepted:
                        keep = False
                        break
                if not keep:
                    self.deck_current.delete(item_id)
        self._apply_treeview_zebra(self.deck_current)
        self._refresh_deck_card_candidates()
        self._render_deck_rules()

    def _deck_add_selected_card(self) -> None:
        selected = self.deck_candidates.selection()
        if not selected:
            return
        key = self._deck_candidate_iid_to_key.get(str(selected[0]))
        if not key:
            return
        try:
            qty = max(1, int(self.deck_qty_var.get() or "1"))
        except Exception:
            qty = 1
        by_name = self._deck_name_to_def()
        card = by_name.get(key)
        if card is not None:
            max_copy = self._max_copies_for_crosses(str(getattr(card, "crosses", "")))
            current = int(self._deck_editor_cards.get(key, 0))
            qty = max(0, min(qty, max_copy - current))
            if qty <= 0:
                messagebox.showwarning("Limite copie", "Hai raggiunto il massimo numero copie per questa carta.")
                return
        self._deck_editor_cards[key] = int(self._deck_editor_cards.get(key, 0)) + qty
        self._refresh_deck_current_list()

    def _on_deck_current_select(self, _event=None) -> None:
        key = self._selected_current_deck_key()
        self._show_deck_effect_from_key(key)

    def _sort_deck_candidates_by(self, column: str) -> None:
        col = str(column or "nome")
        if self._deck_candidates_sort_col == col:
            self._deck_candidates_sort_asc = not self._deck_candidates_sort_asc
        else:
            self._deck_candidates_sort_col = col
            self._deck_candidates_sort_asc = True
        self._refresh_deck_card_candidates()

    def _sort_deck_current_by(self, column: str) -> None:
        col = str(column or "nome")
        if self._deck_current_sort_col == col:
            self._deck_current_sort_asc = not self._deck_current_sort_asc
        else:
            self._deck_current_sort_col = col
            self._deck_current_sort_asc = True
        self._refresh_deck_current_list()

    def _selected_current_deck_key(self) -> str | None:
        sel = self.deck_current.selection()
        if not sel:
            return None
        return self._deck_current_iid_to_key.get(str(sel[0]))

    def _deck_adjust_selected_card(self, delta: int) -> None:
        key = self._selected_current_deck_key()
        if key is None:
            return
        new_qty = int(self._deck_editor_cards.get(key, 0)) + int(delta)
        if new_qty <= 0:
            self._deck_editor_cards.pop(key, None)
        else:
            self._deck_editor_cards[key] = new_qty
        self._refresh_deck_current_list()

    def _deck_remove_selected_card(self) -> None:
        key = self._selected_current_deck_key()
        if key is None:
            return
        self._deck_editor_cards.pop(key, None)
        self._refresh_deck_current_list()

    def _deck_manager_save(self) -> None:
        name = str(self.deck_name_var.get() or "").strip()
        religion = str(self.deck_religion_var.get() or "").strip()
        if not name:
            messagebox.showwarning("Deck", "Inserisci un nome deck.")
            return
        if not religion:
            messagebox.showwarning("Deck", "Seleziona una religione.")
            return
        hard, _soft, _total, _stats = self._deck_rules_report()
        if hard:
            messagebox.showwarning("Deck non valido", "\n".join(hard))
            return

        by_name = self._deck_name_to_def()
        cards_payload = []
        for key in sorted(self._deck_editor_cards.keys()):
            qty = int(self._deck_editor_cards.get(key, 0))
            if qty <= 0:
                continue
            card = by_name.get(key)
            if card is None:
                continue
            cards_payload.append({"name": str(card.name), "qty": qty})

        if self._deck_editor_selected_id is None:
            base = self._norm(name).replace(" ", "_")
            if not base:
                base = "deck"
            self._deck_editor_selected_id = f"user_{base}"

        payload = self._premades_payload()
        kept = [d for d in payload.get("decks", []) if str(d.get("id", "")) != self._deck_editor_selected_id]
        kept.append(
            {
                "id": self._deck_editor_selected_id,
                "religion": religion,
                "name": name,
                "allow_over_45": True,
                "cards": cards_payload,
            }
        )
        payload["decks"] = kept
        self._save_premades_payload(payload)
        reset_runtime_premades()
        self._load_premades_into_runtime()
        self.update_premade_options()
        self._deck_manager_reload_user_decks()
        messagebox.showinfo("Deck", "Deck salvato.")

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

        ttk.Label(win, text=prompt, wraplength=660).pack(anchor="w", padx=8, pady=(8, 4))

        if allow_multi:
            lim = ""
            if min_targets > 0 and max_targets is not None and min_targets == max_targets:
                lim = f" (seleziona esattamente {min_targets})"
            elif max_targets is not None:
                lim = f" (min {min_targets}, max {max_targets})"
            ttk.Label(
                win,
                text=f"Puoi selezionare dalla lista o cliccando sul campo{lim}.",
            ).pack(anchor="w", padx=8, pady=(0, 4))
        else:
            ttk.Label(
                win,
                text="Puoi selezionare dalla lista o cliccando sul campo.",
            ).pack(anchor="w", padx=8, pady=(0, 4))

        counter_var = tk.StringVar(value="")
        selected_var = tk.StringVar(value="Nessun bersaglio selezionato.")
        ttk.Label(win, textvariable=counter_var).pack(anchor="w", padx=8)
        ttk.Label(win, textvariable=selected_var, wraplength=660).pack(anchor="w", padx=8, pady=(4, 8))

        lb = tk.Listbox(win, selectmode=("multiple" if allow_multi else "browse"))
        lb.pack(fill="both", expand=True, padx=8, pady=6)

        for label, _token in normalized_choices:
            lb.insert(tk.END, label)

        token_to_index = {token: i for i, (_label, token) in enumerate(normalized_choices)}

        manual_var = tk.StringVar(value="")
        if allow_manual:
            row = ttk.Frame(win)
            row.pack(fill="x", padx=8, pady=(0, 4))
            ttk.Label(row, text="Valore manuale (opzionale):").pack(side="left")
            ttk.Entry(row, textvariable=manual_var).pack(side="left", fill="x", expand=True, padx=6)

        btn_bar = ttk.Frame(win)
        btn_bar.pack(fill="x", padx=8, pady=8)
        btn_ok = ttk.Button(btn_bar, text="OK")
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
            ttk.Button(btn_bar, text="Senza Target", command=_no_target).pack(side="left", padx=6)
        ttk.Button(btn_bar, text="Annulla", command=_cancel).pack(side="left", padx=6)

        win.protocol("WM_DELETE_WINDOW", _cancel)
        _refresh_state()
        self.wait_window(win)
        return (result["value"] == "", result["value"])

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

    def _card_allows_multi_target(self, uid: str) -> bool:
        mode = self._play_targeting_mode(uid)

        # Compatibilità con il vecchio sistema
        if mode == "multi":
            return True

        # Nuovo sistema guidato: guarda il target vero della carta
        target = self._first_play_target_spec(uid)
        if target is None:
            return False

        if target.type == "selected_targets":
            return True

        max_targets = target.max_targets if target.max_targets is not None else 1
        return max_targets != 1

    def _card_requires_target(self, uid: str) -> bool:
        mode = self._play_targeting_mode(uid)

        if mode in {
            "own_saint",
            "opponent_saint",
            "own_graveyard_saint",
            "manual",
            "multi",
            "monsone",
            "guided",
        }:
            return True

        if mode in {"none", "", None, "auto"}:
            target = self._first_play_target_spec(uid)
            return target is not None

        return False
    
    def _count_cards_from_rule(self, uid: str, rule: dict) -> int:
        if self.engine is None:
            return 0

        own_idx = self.current_human_idx() or 0
        st = self.engine.state
        own = st.players[own_idx]
        opp = st.players[1 - own_idx]

        spec = rule.get("count_cards_controlled_by_owner")
        if not spec:
            return 0

        owner_key = str(spec.get("owner", "me")).strip().lower()
        zone = str(spec.get("zone", "field")).strip().lower()
        filt = spec.get("card_filter", {}) or {}

        player = own if owner_key in {"me", "owner", "controller"} else opp

        card_type_in = {x.lower().strip() for x in filt.get("card_type_in", [])}
        name_contains = filt.get("name_contains")
        name_not_contains = filt.get("name_not_contains")
        crosses_gte = filt.get("crosses_gte")
        crosses_lte = filt.get("crosses_lte")
        strength_gte = filt.get("strength_gte")
        strength_lte = filt.get("strength_lte")

        if zone == "field":
            pool = [x for x in list(player.attack) + list(player.defense) if x is not None]
        elif zone == "graveyard":
            pool = list(player.graveyard)
        elif zone == "hand":
            pool = list(player.hand)
        elif zone in {"deck", "relicario"}:
            pool = list(player.deck)
        else:
            pool = []

        total = 0
        for c_uid in pool:
            inst = st.instances.get(c_uid)
            if inst is None:
                continue

            name_variants = _card_name_variants(inst.definition)
            name_haystack = _card_name_haystack(inst.definition)
            ctype = inst.definition.card_type.lower().strip()
            crosses = getattr(inst.definition, "crosses", None)

            if card_type_in and ctype not in card_type_in:
                continue
            if name_contains and _norm(name_contains) not in name_haystack:
                continue
            if name_not_contains and _norm(name_not_contains) in name_haystack:
                continue
            if crosses_gte is not None and (crosses is None or crosses < int(crosses_gte)):
                continue
            if crosses_lte is not None and (crosses is None or crosses > int(crosses_lte)):
                continue
            eff_strength = self.engine.get_effective_strength(c_uid)
            if strength_gte is not None and eff_strength < int(strength_gte):
                continue
            if strength_lte is not None and eff_strength > int(strength_lte):
                continue

            total += 1

        return total

    def _first_activate_target_spec(self, uid: str):
        script = self._card_script(uid)
        if script is None:
            return None
        for action in script.on_activate_actions:
            target = action.target
            ttype = str(target.type or "").strip().lower()
            if ttype in {"selected_target", "selected_targets"}:
                return target
        return None

    def _target_selection_limits(self, uid: str, *, for_activate: bool = False) -> tuple[int, int | None]:
        mode = self._play_targeting_mode(uid)

        # Nuovo sistema: solo se esiste davvero un target nello script
        target = self._first_activate_target_spec(uid) if for_activate else self._first_play_target_spec(uid)
        if target is not None:
            min_targets = target.min_targets if target.min_targets is not None else 1

            if target.max_targets_from:
                max_targets = self._count_cards_from_rule(uid, target.max_targets_from)
            else:
                max_targets = target.max_targets if target.max_targets is not None else 1

            return (min_targets, max_targets)

        # Compatibilità con i mode vecchi
        if mode == "multi":
            return (1, None)
        if mode in {"own_saint", "opponent_saint", "own_graveyard_saint", "manual"}:
            return (1, 1)
        if mode == "monsone":
            return (0, 3)

        # Carte senza target, tipo Concentrazione
        return (0, 0)

    def _is_monsone_card(self, uid: str) -> bool:
        return self._play_targeting_mode(uid) == "monsone"

    def _guided_target_candidates(self, uid: str) -> list[str]:
        if self.engine is None:
            return []

        engine = self.engine
        own_idx = self.current_human_idx() or 0
        own = engine.state.players[own_idx]
        opp = engine.state.players[1 - own_idx]
        mode = self._play_targeting_mode(uid)
        out: list[str] = []

        # Compatibilità con i mode vecchi
        if mode == "own_graveyard_saint":
            for c_uid in own.graveyard:
                inst = self.engine.state.instances[c_uid]
                if inst.definition.card_type.lower().strip() == "santo":
                    out.append(c_uid)
            return out

        if mode == "own_saint":
            for i in range(3):
                if own.attack[i] is not None:
                    out.append(f"a{i+1}")
                if own.defense[i] is not None:
                    out.append(f"d{i+1}")
            return out

        if mode == "manual":
            return []

        # Nuovo targeting guidato data-driven
        target = self._first_play_target_spec(uid)
        if target is None:
            return []

        owner_key = str(target.owner or "me").strip().lower()
        if owner_key in {"any", "both", "all", "either"}:
            players = [own, opp]
        elif owner_key in {"me", "owner", "controller"}:
            players = [own]
        else:
            players = [opp]

        zones = [z.lower().strip() for z in (target.zones or []) if str(z).strip()]
        if not zones:
            zones = [str(target.zone or "field").strip().lower()]

        type_filter = {x.lower().strip() for x in target.card_filter.card_type_in}
        name_in = {str(x).lower().strip() for x in (target.card_filter.name_in or []) if str(x).strip()}
        name_equals = target.card_filter.name_equals.lower().strip() if target.card_filter.name_equals else None
        name_contains = target.card_filter.name_contains.lower().strip() if target.card_filter.name_contains else None
        name_not_contains = target.card_filter.name_not_contains.lower().strip() if target.card_filter.name_not_contains else None
        crosses_gte = target.card_filter.crosses_gte
        crosses_lte = target.card_filter.crosses_lte
        strength_gte = target.card_filter.strength_gte
        strength_lte = target.card_filter.strength_lte

        exclude_buildings_if_my_building_zone_occupied = (
            target.card_filter.exclude_buildings_if_my_building_zone_occupied
        )

        def matches(inst) -> bool:
            ctype = inst.definition.card_type.lower().strip()
            name_variants = _card_name_variants(inst.definition)
            name_haystack = _card_name_haystack(inst.definition)
            crosses = getattr(inst.definition, "crosses", None)

            if type_filter and ctype not in type_filter:
                return False
            if name_in and name_in.isdisjoint(name_variants):
                return False
            if name_equals and _norm(name_equals) not in name_variants:
                return False

            if name_contains and _norm(name_contains) not in name_haystack:
                return False

            if name_not_contains and _norm(name_not_contains) in name_haystack:
                return False

            if (
                exclude_buildings_if_my_building_zone_occupied
                and own.building is not None
                and ctype == "edificio"
            ):
                return False

            if crosses_gte is not None and (crosses is None or crosses < crosses_gte):
                return False

            if crosses_lte is not None and (crosses is None or crosses > crosses_lte):
                return False

            eff_strength = engine.get_effective_strength(inst.uid)
            if strength_gte is not None and eff_strength < int(strength_gte):
                return False
            if strength_lte is not None and eff_strength > int(strength_lte):
                return False

            return True

        seen: set[str] = set()

        for player in players:
            for zone in zones:
                if zone == "field":
                    for i in range(3):
                        a_uid = player.attack[i]
                        if a_uid is not None:
                            inst = engine.state.instances[a_uid]
                            if matches(inst):
                                token = a_uid
                                if token not in seen:
                                    out.append(token)
                                    seen.add(token)

                        d_uid = player.defense[i]
                        if d_uid is not None:
                            inst = engine.state.instances[d_uid]
                            if matches(inst):
                                token = d_uid
                                if token not in seen:
                                    out.append(token)
                                    seen.add(token)
                    for i in range(4):
                        r_uid = player.artifacts[i]
                        if r_uid is not None:
                            inst = engine.state.instances[r_uid]
                            if matches(inst):
                                token = r_uid
                                if token not in seen:
                                    out.append(token)
                                    seen.add(token)
                    b_uid = player.building
                    if b_uid is not None:
                        inst = engine.state.instances[b_uid]
                        if matches(inst):
                            token = b_uid
                            if token not in seen:
                                out.append(token)
                                seen.add(token)

                elif zone == "graveyard":
                    for c_uid in player.graveyard:
                        inst = engine.state.instances[c_uid]
                        if matches(inst) and c_uid not in seen:
                            out.append(c_uid)
                            seen.add(c_uid)

                elif zone == "excommunicated":
                    for c_uid in player.excommunicated:
                        inst = engine.state.instances[c_uid]
                        if matches(inst) and c_uid not in seen:
                            out.append(c_uid)
                            seen.add(c_uid)

                elif zone == "hand":
                    for c_uid in player.hand:
                        inst = engine.state.instances[c_uid]
                        if matches(inst) and c_uid not in seen:
                            out.append(c_uid)
                            seen.add(c_uid)

                elif zone in {"deck", "relicario"}:
                    for c_uid in player.deck:
                        inst = engine.state.instances[c_uid]
                        if matches(inst) and c_uid not in seen:
                            out.append(c_uid)
                            seen.add(c_uid)

        return out
    
    def _guided_target_candidates_for_spec(self, uid: str, target) -> list[str]:
        if self.engine is None:
            return []

        engine = self.engine
        own_idx = self.current_human_idx() or 0
        own = engine.state.players[own_idx]
        opp = engine.state.players[1 - own_idx]
        out: list[str] = []

        owner_key = str(target.owner or "me").strip().lower()
        if owner_key in {"any", "both", "all", "either"}:
            players = [own, opp]
        elif owner_key in {"me", "owner", "controller"}:
            players = [own]
        else:
            players = [opp]

        zones = [z.lower().strip() for z in (target.zones or []) if str(z).strip()]
        if not zones:
            zones = [str(target.zone or "field").strip().lower()]

        type_filter = {x.lower().strip() for x in target.card_filter.card_type_in}
        name_in = {str(x).lower().strip() for x in (target.card_filter.name_in or []) if str(x).strip()}
        name_equals = target.card_filter.name_equals.lower().strip() if target.card_filter.name_equals else None
        name_contains = target.card_filter.name_contains.lower().strip() if target.card_filter.name_contains else None
        name_not_contains = target.card_filter.name_not_contains.lower().strip() if target.card_filter.name_not_contains else None
        crosses_gte = target.card_filter.crosses_gte
        crosses_lte = target.card_filter.crosses_lte
        strength_gte = target.card_filter.strength_gte
        strength_lte = target.card_filter.strength_lte

        exclude_buildings_if_my_building_zone_occupied = (
            target.card_filter.exclude_buildings_if_my_building_zone_occupied
        )

        def matches(inst_uid: str) -> bool:
            inst = engine.state.instances[inst_uid]
            ctype = inst.definition.card_type.lower().strip()
            name_variants = _card_name_variants(inst.definition)
            name_haystack = _card_name_haystack(inst.definition)

            if target.card_filter.exclude_event_card and inst_uid == uid:
                return False
            if type_filter and ctype not in type_filter:
                return False
            if name_in and name_in.isdisjoint(name_variants):
                return False
            if name_equals and _norm(name_equals) not in name_variants:
                return False
            if name_contains and _norm(name_contains) not in name_haystack:
                return False
            if name_not_contains and _norm(name_not_contains) in name_haystack:
                return False
            if (
                exclude_buildings_if_my_building_zone_occupied
                and own.building is not None
                and ctype == "edificio"
            ):
                return False

            crosses = getattr(inst.definition, "crosses", None)
            if crosses_gte is not None and (crosses is None or crosses < crosses_gte):
                return False
            if crosses_lte is not None and (crosses is None or crosses > crosses_lte):
                return False
            eff_strength = engine.get_effective_strength(inst_uid)
            if strength_gte is not None and eff_strength < int(strength_gte):
                return False
            if strength_lte is not None and eff_strength > int(strength_lte):
                return False
            return True

        seen: set[str] = set()

        for player in players:
            for zone in zones:
                if zone == "field":
                    for i in range(3):
                        a_uid = player.attack[i]
                        if a_uid is not None and matches(a_uid):
                            token = a_uid
                            if token not in seen:
                                out.append(token)
                                seen.add(token)

                        d_uid = player.defense[i]
                        if d_uid is not None and matches(d_uid):
                            token = d_uid
                            if token not in seen:
                                out.append(token)
                                seen.add(token)

                    for i in range(len(player.artifacts)):
                        r_uid = player.artifacts[i]
                        if r_uid is not None and matches(r_uid):
                            token = r_uid
                            if token not in seen:
                                out.append(token)
                                seen.add(token)

                    if player.building is not None and matches(player.building):
                        token = player.building
                        if token not in seen:
                            out.append(token)
                            seen.add(token)

                elif zone == "graveyard":
                    for c_uid in player.graveyard:
                        if matches(c_uid) and c_uid not in seen:
                            out.append(c_uid)
                            seen.add(c_uid)

                elif zone == "excommunicated":
                    for c_uid in player.excommunicated:
                        if matches(c_uid) and c_uid not in seen:
                            out.append(c_uid)
                            seen.add(c_uid)

                elif zone == "hand":
                    for c_uid in player.hand:
                        if matches(c_uid) and c_uid not in seen:
                            out.append(c_uid)
                            seen.add(c_uid)

                elif zone in {"deck", "relicario"}:
                    for c_uid in player.deck:
                        if matches(c_uid) and c_uid not in seen:
                            out.append(c_uid)
                            seen.add(c_uid)

        return out

    def _board_activation_candidates(self, player_idx: int) -> list[str]:
        if self.engine is None:
            return []
        own = self.engine.state.players[player_idx]
        opp = self.engine.state.players[1 - player_idx]
        out: list[str] = []
        for i in range(3):
            if own.attack[i] is not None:
                out.append(f"s:a{i+1}")
            if opp.attack[i] is not None:
                out.append(f"o:a{i+1}")
        for i in range(3):
            if own.defense[i] is not None:
                out.append(f"s:d{i+1}")
            if opp.defense[i] is not None:
                out.append(f"o:d{i+1}")
        for i in range(4):
            if own.artifacts[i] is not None:
                out.append(f"s:r{i+1}")
            if opp.artifacts[i] is not None:
                out.append(f"o:r{i+1}")
        if own.building is not None:
            out.append("s:b")
        if opp.building is not None:
            out.append("o:b")
        return out

    def _format_guided_candidate(self, token: str, own_idx: int) -> str:
        if self.engine is None:
            return token
        st = self.engine.state
        own = st.players[own_idx]
        opp = st.players[1 - own_idx]
        raw = str(token or "").strip()
        side = ""
        core = raw
        if ":" in raw:
            pref, code = raw.split(":", 1)
            p = pref.strip().lower()
            if p in {"s", "self", "me", "own", "owner", "controller"}:
                side = "TUO"
                core = code.strip()
            elif p in {"o", "opp", "enemy", "opponent", "other"}:
                side = "AVV"
                core = code.strip()
        chosen_player = own if side != "AVV" else opp
        side_prefix = f"[{side}] " if side else ""
        if core.startswith("a") and len(core) == 2 and core[1].isdigit():
            i = int(core[1]) - 1
            uid = chosen_player.attack[i] if 0 <= i < 3 else None
            name = st.instances[uid].definition.name if uid is not None else "-"
            return f"{side_prefix}Attacco {i + 1} | {name}"
        if core.startswith("d") and len(core) == 2 and core[1].isdigit():
            i = int(core[1]) - 1
            uid = chosen_player.defense[i] if 0 <= i < 3 else None
            name = st.instances[uid].definition.name if uid is not None else "-"
            return f"{side_prefix}Difesa {i + 1} | {name}"
        if core.startswith("r") and len(core) == 2 and core[1].isdigit():
            i = int(core[1]) - 1
            uid = chosen_player.artifacts[i] if 0 <= i < 4 else None
            name = st.instances[uid].definition.name if uid is not None else "-"
            return f"{side_prefix}Artefatto {i + 1} | {name}"
        if core == "b":
            uid = chosen_player.building
            name = st.instances[uid].definition.name if uid else "-"
            return f"{side_prefix}Edificio | {name}"
        if ":" in token:
            pref, name = token.split(":", 1)
            if pref == "deck":
                return f"Reliquiario | {name}"
            if pref == "grave":
                return f"Cimitero | {name}"
            if pref == "excom":
                return f"Scomunicate | {name}"
            return f"{pref} | {name}"

        if token in st.instances:
            inst = st.instances[token]
            owner = "TUO" if inst.owner == own_idx else "AVV"
            p = st.players[inst.owner]
            where = "fuori campo"
            for i, c_uid in enumerate(p.attack):
                if c_uid == token:
                    where = f"Attacco {i + 1}"
                    break
            if where == "fuori campo":
                for i, c_uid in enumerate(p.defense):
                    if c_uid == token:
                        where = f"Difesa {i + 1}"
                        break
            if where == "fuori campo":
                for i, c_uid in enumerate(p.artifacts):
                    if c_uid == token:
                        where = f"Artefatto {i + 1}"
                        break
            if where == "fuori campo" and p.building == token:
                where = "Edificio"
            return f"{owner} {where} | {inst.definition.name} ({inst.definition.card_type})"

        return token

    def _monsone_target_payload(self, spell_uid: str) -> tuple[bool, str | None]:
        if self.engine is None:
            return (True, None)
        own_idx = self.current_human_idx() or 0
        player = self.engine.state.players[own_idx]

        hand_choices: list[tuple[str, str]] = []
        for h_uid in player.hand:
            if h_uid == spell_uid:
                continue
            c = self.engine.state.instances[h_uid].definition
            hand_choices.append((f"{c.name} ({c.card_type})", h_uid))

        canceled, picked_hand = self._open_board_target_picker(
            title="Monsone - Scarto",
            prompt="Seleziona fino a 3 carte dalla tua mano da mandare al cimitero.",
            choices=hand_choices,
            allow_multi=True,
            min_targets=0,
            max_targets=3,
            allow_none=True,
            allow_manual=False,
        )
        if canceled:
            return (True, None)
        discard_uids: list[str] = []
        if picked_hand:
            discard_uids = [x for x in picked_hand.split(",") if x]

        field_choices: list[tuple[str, str]] = []
        for p_idx in (0, 1):
            side = "Tuo campo" if p_idx == own_idx else "Campo avversario"
            p = self.engine.state.players[p_idx]
            for i, s_uid in enumerate(p.attack):
                if not s_uid:
                    continue
                inst = self.engine.state.instances[s_uid]
                try:
                    crosses = int(float(inst.definition.crosses))
                except (ValueError, TypeError):
                    crosses = 99
                if crosses <= 8:
                    field_choices.append((f"{side} Attacco {i+1} | {inst.definition.name} (Croci {inst.definition.crosses})", s_uid))
            for i, s_uid in enumerate(p.defense):
                if not s_uid:
                    continue
                inst = self.engine.state.instances[s_uid]
                try:
                    crosses = int(float(inst.definition.crosses))
                except (ValueError, TypeError):
                    crosses = 99
                if crosses <= 8:
                    field_choices.append((f"{side} Difesa {i+1} | {inst.definition.name} (Croci {inst.definition.crosses})", s_uid))
            for i, a_uid in enumerate(p.artifacts):
                if not a_uid:
                    continue
                inst = self.engine.state.instances[a_uid]
                try:
                    crosses = int(float(inst.definition.crosses))
                except (ValueError, TypeError):
                    crosses = 99
                if crosses <= 8:
                    field_choices.append((f"{side} Artefatto {i+1} | {inst.definition.name} (Croci {inst.definition.crosses})", a_uid))
            if p.building:
                b_uid = p.building
                inst = self.engine.state.instances[b_uid]
                try:
                    crosses = int(float(inst.definition.crosses))
                except (ValueError, TypeError):
                    crosses = 99
                if crosses <= 8:
                    field_choices.append((f"{side} Edificio | {inst.definition.name} (Croci {inst.definition.crosses})", b_uid))

        canceled, picked_field = self._open_board_target_picker(
            title="Monsone - Ritorno al Reliquiario",
            prompt="Seleziona fino a 3 carte sul terreno (Croci <= 8) da rimettere nei reliquiari dei rispettivi proprietari.",
            choices=field_choices,
            allow_multi=True,
            min_targets=0,
            max_targets=3,
            allow_none=True,
            allow_manual=False,
        )
        if canceled:
            return (True, None)
        return_uids: list[str] = []
        if picked_field:
            return_uids = [x for x in picked_field.split(",") if x]

        target = f"monsone:discard={','.join(discard_uids)};return={','.join(return_uids)}"
        return (False, target)

    
    
    def _collect_on_play_action_targets(self, uid: str) -> tuple[bool, str | None]:
        if self.engine is None:
            return (True, None)

        own_idx = self.current_human_idx() or 0
        manual_actions = self._manual_play_target_actions(uid)
        if not manual_actions:
            return (False, None)

        picked_parts: list[str] = []

        for action_idx, target_spec in manual_actions:
            candidates = self._guided_target_candidates_for_spec(uid, target_spec)

            min_targets = target_spec.min_targets if target_spec.min_targets is not None else 1
            if target_spec.max_targets_from:
                max_targets = self._count_cards_from_rule(uid, target_spec.max_targets_from)
            else:
                max_targets = target_spec.max_targets if target_spec.max_targets is not None else 1

            allow_none = (min_targets == 0)
            multi = str(target_spec.type or "").strip().lower() == "selected_targets" or max_targets != 1

            if not candidates:
                if allow_none:
                    picked_parts.append(f"{action_idx}=")
                    continue
                messagebox.showwarning("Selezione Bersaglio", "Nessun bersaglio valido disponibile per questa parte dell'effetto.")
                return (True, None)

            choices = [(self._format_guided_candidate(c, own_idx), c) for c in candidates]

            canceled, selected = self._open_board_target_picker(
                title="Selezione Bersaglio",
                prompt="Seleziona i bersagli validi dalla lista oppure cliccando sul campo.",
                choices=choices,
                allow_multi=multi,
                min_targets=min_targets,
                max_targets=max_targets,
                allow_none=allow_none,
                allow_manual=False,
                card_uid=uid,
            )

            if canceled:
                return (True, None)

            picked_parts.append(f"{action_idx}={selected or ''}")

        payload = "seq:" + ";;".join(picked_parts)
        return (False, payload)

    def ask_guided_quick_target(self, uid: str) -> None:
        if self._is_monsone_card(uid):
            canceled, target = self._monsone_target_payload(uid)
            if canceled:
                return
            self.play_uid(uid, target)
            return

        manual_actions = self._manual_play_target_actions(uid)
        if len(manual_actions) > 1:
            canceled, payload = self._collect_on_play_action_targets(uid)
            if canceled:
                return
            self.play_uid(uid, payload)
            return

        if not self._card_requires_target(uid):
            self.play_uid(uid, None)
            return
        if self.engine is None:
            return
        own_idx = self.current_human_idx() or 0
        hand = self.engine.state.players[own_idx].hand
        if uid not in hand:
            return
        hand_idx = hand.index(uid)
        is_quick = self.chain_active
        candidates = self._guided_target_candidates(uid)
        candidates = [c for c in candidates if self._can_play_target(own_idx, hand_idx, c, quick=is_quick)]
        multi = self._card_allows_multi_target(uid)
        min_targets, max_targets = self._target_selection_limits(uid)
        allow_none = self._can_play_target(own_idx, hand_idx, None, quick=is_quick)
        mode = self._play_targeting_mode(uid)
        choices = [(self._format_guided_candidate(c, own_idx), c) for c in candidates]
        if not choices:
            if mode == "manual":
                canceled, selected = self._open_board_target_picker(
                    title="Selezione Bersaglio",
                    prompt="Inserisci manualmente il bersaglio della carta.",
                    choices=[],
                    allow_multi=False,
                    min_targets=0,
                    max_targets=1,
                    allow_none=allow_none,
                    allow_manual=True,
                )
                if canceled:
                    return
                self.play_uid(uid, selected)
                return
            if allow_none:
                self.play_uid(uid, None)
                return
            messagebox.showwarning("Selezione Bersaglio", "Nessun bersaglio valido disponibile per questa carta.")
            return
    
        canceled, selected = self._open_board_target_picker(
            title="Selezione Bersaglio",
            prompt="Seleziona i bersagli validi dalla lista oppure cliccando sul campo.",
            choices=choices,
            allow_multi=multi,
            min_targets=min_targets,
            max_targets=max_targets,
            allow_none=allow_none,
            allow_manual=False,
            card_uid=uid,
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
        self._clear_slot_highlights()
        own_idx = self.current_human_idx() or 0
        uid = self.engine.resolve_board_uid(own_idx, source)
        if uid is None:
            return
        menu = tk.Menu(self, tearoff=0)
        can_open_attack_menu = source.startswith("a") or source.startswith("d")
        if can_open_attack_menu:
            slot = int(source[1])
            from_slot = slot - 1 if source.startswith("a") else -slot
            m_attack = tk.Menu(menu, tearoff=0)
            valid_slots = self._valid_attack_targets(own_idx, from_slot)
            hl_tokens: list[str] = []
            for t_slot in valid_slots:
                if t_slot is None:
                    m_attack.add_command(label="Attacco diretto", command=lambda fs=from_slot: self.do_attack(fs, None))
                else:
                    t = t_slot + 1
                    m_attack.add_command(label=f"Target t{t}", command=lambda fs=from_slot, tt=t: self.do_attack(fs, tt - 1))
                    hl_tokens.append(f"a{t}")
            if not valid_slots:
                m_attack.add_command(label="Nessun bersaglio attaccabile", state="disabled")
            menu.add_cascade(label="Attacca", menu=m_attack)
            if hl_tokens:
                self._set_slot_highlights(hl_tokens, side_hint="enemy")
        has_activation = self._activation_has_any_valid_option(own_idx, source)
        if has_activation:
            menu.add_command(label="Attiva abilita", command=lambda src=source: self.do_activate(src))
        else:
            menu.add_command(label="Attiva abilita", state="disabled")
        equipped_uids = self._equipped_uids_for(uid)
        if equipped_uids:
            m_equipped = tk.Menu(menu, tearoff=0)
            for eq_uid in equipped_uids:
                eq_inst = self.engine.state.instances.get(eq_uid)
                if eq_inst is None:
                    continue
                eq_name = eq_inst.definition.name
                m_equipped.add_command(
                    label=eq_name,
                    command=lambda e_uid=eq_uid: self.show_card_detail(e_uid),
                )
            if m_equipped.index("end") is not None:
                menu.add_separator()
                menu.add_cascade(label="Carte Equipaggiate", menu=m_equipped)
        menu.bind("<Unmap>", lambda _e: self._clear_slot_highlights())
        try:
            menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
        finally:
            menu.grab_release()

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
        if uid is None:
            messagebox.showwarning("Abilita non valida", "Sorgente non valida.")
            return
        mode = self._activate_targeting_mode(uid)
        if mode == "none":
            res = self.engine.activate_ability(own_idx, source, None)
            if res.ok and bool(self.engine.state.flags.get("_runtime_waiting_for_reveal")):
                self._post_reveal_chain_actor = own_idx
                self._maybe_show_runtime_reveal()
                self.begin_turn_if_needed()
                return
            if res.ok:
                self.start_chain(actor_idx=own_idx)
            if not res.ok:
                messagebox.showwarning("Abilita non valida", res.message)
            self.refresh()
            self.begin_turn_if_needed()
            return
        if mode == "manual":
            target_spec = self._first_activate_target_spec(uid)
            if target_spec is not None:
                candidates = self._guided_target_candidates_for_spec(uid, target_spec)
                choices = [(self._format_guided_candidate(c, own_idx), c) for c in candidates]
                min_targets = target_spec.min_targets if target_spec.min_targets is not None else 1
                if target_spec.max_targets_from:
                    max_targets = self._count_cards_from_rule(uid, target_spec.max_targets_from)
                else:
                    max_targets = target_spec.max_targets if target_spec.max_targets is not None else 1
                allow_none = min_targets == 0 and self._can_activate_target(own_idx, source, None)
                if not choices and not allow_none:
                    messagebox.showwarning("Abilita non valida", "Nessun bersaglio valido disponibile.")
                    return
                canceled, target = self._open_board_target_picker(
                    title="Attiva Abilita",
                    prompt="Seleziona un bersaglio valido per l'abilita.",
                    choices=choices,
                    allow_multi=(max_targets is None or max_targets > 1),
                    min_targets=min_targets,
                    max_targets=max_targets,
                    allow_none=allow_none,
                    allow_manual=False,
                    card_uid=uid,
                )
                if canceled:
                    return
            else:
                canceled, target = self._open_board_target_picker(
                    title="Attiva Abilita",
                    prompt="Inserisci manualmente il bersaglio dell'abilita.",
                    choices=[],
                    allow_multi=False,
                    min_targets=0,
                    max_targets=1,
                    allow_none=True,
                    allow_manual=True,
                    card_uid=uid,
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
            return
        min_targets, max_targets = self._target_selection_limits(uid, for_activate=True)
        valid_tokens = self._valid_activation_targets(own_idx, source, uid)
        allow_no_target = self._can_activate_target(own_idx, source, None)

        valid_tokens = [
            tok
            for tok in valid_tokens
            if (
                not self._is_board_token(tok)
                or self._resolve_highlight_widget(tok, own_idx=own_idx, side_hint="auto", card_uid=uid) is not None
            )
        ]

        if not valid_tokens and not allow_no_target:
            messagebox.showwarning("Abilita non valida", "Nessun bersaglio valido disponibile.")
            return

        choices = [(self._format_guided_candidate(c, own_idx), c) for c in valid_tokens]
        canceled, target = self._open_board_target_picker(
            title="Attiva Abilita",
            prompt="Seleziona un bersaglio valido per l'abilita dalla lista oppure cliccando sul campo.",
            choices=choices,
            allow_multi=(max_targets is None or max_targets > 1),
            min_targets=min_targets,
            max_targets=max_targets,
            allow_none=allow_no_target,
            allow_manual=False,
            card_uid=uid,
        )
        if canceled:
            return
        res = self.engine.activate_ability(own_idx, source, target)
        if res.ok and bool(self.engine.state.flags.get("_runtime_waiting_for_reveal")):
            self._post_reveal_chain_actor = own_idx
            self._maybe_show_runtime_reveal()
            self.begin_turn_if_needed()
            return
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
    parser.add_argument("--cards-json", type=str, default=str(DEFAULT_JSON), help="Cache JSON carte")
    parser.add_argument("--premades-json", type=str, default=None, help="Importa deck premade custom da JSON")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--ai-delay", type=float, default=1.0)
    return parser


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
