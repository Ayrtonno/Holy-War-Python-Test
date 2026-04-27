from __future__ import annotations
# pyright: reportAttributeAccessIssue=false

import json
from typing import TYPE_CHECKING, Any, cast
import tkinter as tk
from tkinter import messagebox, ttk

from holywar.data.deck_builder import runtime_premade_decks, reset_runtime_premades, register_premades_from_json
from holywar.effects.runtime import _norm

# Deck manager UI, filters, validation and persistence helpers.
class GUIDeckManagerMixin:
    """Deck editor UI, filters, validation and persistence helpers."""

    if TYPE_CHECKING:
        def __getattr__(self, _name: str) -> Any: ...

    # Builds the deck manager UI components and layout.
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
    # Normalizes card names for consistent lookup, handling common character encoding issues and applying a general normalization function.
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

    # Parses the cross value from a card's crosses attribute, handling both numeric and "Croce Bianca" cases, and returns None for invalid inputs.
    def _cross_value(self, crosses: str) -> int | None:
        txt = str(crosses or "").strip().lower()
        if txt in {"white", "croce bianca"}:
            return 11
        try:
            return int(float(txt))
        except Exception:
            return None

    # Determines the maximum allowed copies of a card in a deck based on its cross value, following specific rules for different rarity bands.
    def _max_copies_for_crosses(self, crosses: str) -> int:
        value = self._cross_value(crosses)
        if value is None:
            return 1
        if 1 <= value <= 3:
            return 5
        if 4 <= value <= 6:
            return 3
        return 1

    # Loads the premade decks from the JSON file, ensuring the structure is valid and returning a dictionary with a "decks" key containing a list of deck dictionaries.
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

    # Saves the given premade decks payload to the JSON file, ensuring the parent directory exists and writing the data with proper formatting and encoding.
    def _save_premades_payload(self, payload: dict) -> None:
        self.premades_path.parent.mkdir(parents=True, exist_ok=True)
        self.premades_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # Loads the premade decks from the JSON file into the runtime, allowing them to be accessed and used within the application.
    def _load_premades_into_runtime(self) -> None:
        if self.premades_path.exists():
            register_premades_from_json(self.premades_path)

    # Creates a mapping of normalized card names to their definitions for quick lookup when validating deck contents against the card catalog.
    def _deck_name_to_def(self) -> dict[str, Any]:
        return {self._norm(c.name): c for c in self.cards}

    # Generates a report on the current deck's compliance with the game rules, checking for total card count, individual card limits based on rarity, and providing feedback on any issues found.
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

    # Renders the deck rules report in the UI, showing total card count, limits based on rarity bands, and any errors or notes related to the current deck composition.
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

    # Reloads the user decks from the runtime, updates the listbox with the current decks, and refreshes the deck rules and card candidates based on the loaded decks.
    def _deck_manager_reload_user_decks(self) -> None:
        self._deck_entries = runtime_premade_decks()
        self.deck_listbox.delete(0, tk.END)
        for deck in self._deck_entries:
            label = f"{deck.get('name', 'Deck')} [{deck.get('religion', '-')}]"
            self.deck_listbox.insert(tk.END, label)
        self._deck_manager_new()
        self._refresh_deck_card_candidates()

    # Creates a new deck by resetting the editor state, clearing the current deck composition, and preparing the UI for a new deck entry.
    def _deck_manager_new(self) -> None:
        self._deck_editor_selected_id = None
        self._deck_editor_cards = {}
        self.deck_name_var.set("")
        if self.religions:
            self.deck_religion_var.set(self.religions[0])
        self.deck_current.delete(*self.deck_current.get_children(""))
        self.deck_listbox.selection_clear(0, tk.END)
        self._render_deck_rules()

    # Deletes the selected deck after confirming with the user, updates the premades payload, and refreshes the UI to reflect the changes.
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

    # Handles the selection of a deck from the listbox, loading its details into the editor fields, parsing the card list, and refreshing the UI to show the selected deck's composition and rules compliance.
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

    # Determines the rarity bucket for a card based on its cross value, categorizing it into specific bands or marking it as "Bianca" for special cases, and returning "?" for invalid inputs.
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

    # Synchronizes the expansion filter options for the deck editor based on the expansions present in the card catalog, ensuring that all available expansions are listed and that the current selection remains valid.
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

    # Parses a numeric filter value from a string, returning an integer if valid or None if the input is empty or cannot be converted to a number, allowing for flexible filtering in the deck editor.
    def _parse_filter_number(self, value: str) -> int | None:
        raw = str(value or "").strip()
        if not raw:
            return None
        try:
            return int(raw)
        except Exception:
            return None

    # Compares a current numeric value against a wanted value using a specified operator, supporting common comparison operators and returning a boolean result based on the comparison, which is used for filtering cards in the deck editor.
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

    # Resets all deck filters to their default states, clearing search terms, resetting dropdowns to "Tutte" or default values, and refreshing the card candidates list to show all cards without any filters applied.
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

    # Opens a dialog for filtering the deck candidates or current deck cards in an Excel-like manner, allowing the user to select a column, search for values, and apply filters based on the unique values present in that column, with options to sort and select/deselect all values.
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

        win = tk.Toplevel(cast(Any, self))
        win.title(title)
        win.transient(cast(Any, self))
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

    # Displays the effect text of a card in the deck editor based on the provided key, looking up the card definition and updating the UI with the card's name and effect description, or showing a default message if no effect text is available.
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

    # Handles the selection of a card from the deck candidates list, retrieving the corresponding card key and displaying its effect text in the UI for the user to review before adding it to the deck.
    def _on_deck_candidates_select(self, _event=None) -> None:
        selected = self.deck_candidates.selection()
        if not selected:
            return
        key = self._deck_candidate_iid_to_key.get(str(selected[0]))
        self._show_deck_effect_from_key(key)

    # Handles the selection of a card from the current deck list, retrieving the corresponding card key and displaying its effect text in the UI for the user to review or modify their deck composition.
    def _selected_tree_key(self, tree: ttk.Treeview, iid_to_key: dict[str, str]) -> str | None:
        sel = tree.selection()
        if not sel:
            return None
        return iid_to_key.get(str(sel[0]))

    # Restores the selection in a treeview based on a given card key, iterating through the items to find a matching key and setting the selection, focus, and visibility accordingly, returning True if successful or False if the key is not found or an error occurs.
    def _restore_tree_selection_by_key(self, tree: ttk.Treeview, iid_to_key: dict[str, str], key: str | None) -> bool:
        if not key:
            return False
        for item_id, item_key in iid_to_key.items():
            if str(item_key) != str(key):
                continue
            try:
                tree.selection_set(item_id)
                tree.focus(item_id)
                tree.see(item_id)
            except tk.TclError:
                return False
            return True
        return False

    # Applies a zebra striping style to the rows of a treeview, configuring tags for even and odd rows with different background colors, and iterating through the items to assign the appropriate tag based on their position in the list.
    def _apply_treeview_zebra(self, tree: ttk.Treeview) -> None:
        tree.tag_configure("even", background=self._deck_palette["surface"])
        tree.tag_configure("odd", background="#fdfcff")
        for pos, item_id in enumerate(tree.get_children("")):
            tree.item(item_id, tags=("even" if (pos % 2 == 0) else "odd",))

    # Refreshes the list of candidate cards for the deck editor based on the current search and filter criteria, sorting options, and the card catalog, updating the treeview with the matching cards and maintaining selection if possible.
    def _refresh_deck_card_candidates(self) -> None:
        selected_key_before = self._selected_tree_key(
            self.deck_candidates,
            getattr(self, "_deck_candidate_iid_to_key", {}),
        )
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
        unique_cards: dict[str, Any] = {}
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
        if self._restore_tree_selection_by_key(self.deck_candidates, self._deck_candidate_iid_to_key, selected_key_before):
            self._show_deck_effect_from_key(selected_key_before)

    # Refreshes the list of cards currently in the deck editor, updating the treeview with the current composition, applying sorting and value filters, and maintaining selection if possible, while also refreshing the card candidates and deck rules based on the current deck state.
    def _refresh_deck_current_list(self) -> None:
        selected_key_before = self._selected_tree_key(
            self.deck_current,
            getattr(self, "_deck_current_iid_to_key", {}),
        )
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
        if self._restore_tree_selection_by_key(self.deck_current, self._deck_current_iid_to_key, selected_key_before):
            self._show_deck_effect_from_key(selected_key_before)
        self._refresh_deck_card_candidates()
        self._render_deck_rules()

    # Adds the selected card from the candidates list to the current deck composition, respecting the maximum allowed copies based on the card's crosses, updating the deck editor state, and refreshing the UI to reflect the changes.
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

    # Handles the selection of a card from the current deck list, allowing the user to adjust its quantity or remove it from the deck, and updating the deck editor state and UI accordingly.
    def _on_deck_current_select(self, _event=None) -> None:
        key = self._selected_current_deck_key()
        self._show_deck_effect_from_key(key)

    # Sorts the deck candidates list based on the specified column, toggling the sort order if the same column is selected again, and refreshing the UI to reflect the new sorting.
    def _sort_deck_candidates_by(self, column: str) -> None:
        col = str(column or "nome")
        if self._deck_candidates_sort_col == col:
            self._deck_candidates_sort_asc = not self._deck_candidates_sort_asc
        else:
            self._deck_candidates_sort_col = col
            self._deck_candidates_sort_asc = True
        self._refresh_deck_card_candidates()

    # Sorts the current deck list based on the specified column, toggling the sort order if the same column is selected again, and refreshing the UI to reflect the new sorting.
    def _sort_deck_current_by(self, column: str) -> None:
        col = str(column or "nome")
        if self._deck_current_sort_col == col:
            self._deck_current_sort_asc = not self._deck_current_sort_asc
        else:
            self._deck_current_sort_col = col
            self._deck_current_sort_asc = True
        self._refresh_deck_current_list()

    # Retrieves the key of the currently selected card in the current deck list, returning None if no selection is made, which is used for displaying card effects and managing deck composition.
    def _selected_current_deck_key(self) -> str | None:
        sel = self.deck_current.selection()
        if not sel:
            return None
        return self._deck_current_iid_to_key.get(str(sel[0]))

    # Adjusts the quantity of the selected card in the current deck by a specified delta, ensuring that the quantity does not drop below zero and refreshing the UI to reflect the changes in the deck composition.
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

    # Removes the selected card from the current deck composition, updating the deck editor state and refreshing the UI to reflect the removal.
    def _deck_remove_selected_card(self) -> None:
        key = self._selected_current_deck_key()
        if key is None:
            return
        self._deck_editor_cards.pop(key, None)
        self._refresh_deck_current_list()

    # Validates the current deck composition against the defined rules, checking for issues such as missing name or religion, and ensuring that the card quantities adhere to the maximum allowed based on their crosses, and displays appropriate warnings if any problems are found.
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
