from __future__ import annotations

from typing import Any, cast
import tkinter as tk
from tkinter import ttk

# This mixin class provides theme and shared visual helpers for GUI screens and popups in the Holy War game. It includes methods for setting up styles for the deck builder, game view, and target picker sections of the GUI, as well as utility methods for applying themes to widgets and centering windows on the screen. The styles are defined using the ttk.Style class, and the mixin ensures a consistent visual appearance across different parts of the application.
class GUIStylesMixin:
    """Theme and shared visual helpers for GUI screens and popups."""

    # The following methods set up styles for different sections of the GUI, including the deck builder, game view, and target picker. Each method defines a color palette and configures styles for various ttk widgets such as frames, labels, buttons, entries, comboboxes, scrollbars, and treeviews. The styles include settings for background colors, foreground colors, border colors, fonts, padding, and state-specific appearances (e.g., active, pressed, disabled). The mixin also includes utility methods for applying themes to widgets and centering windows on the screen.
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
        style = ttk.Style(cast(Any, self))
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
        cast(Any, style).layout(
            "Deck.Vertical.TScrollbar",
            [("Vertical.Scrollbar.trough", {"sticky": "ns", "children": [("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]})],
        )
        cast(Any, style).layout(
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

    # This method sets up the styles for the main game view, defining a color palette and configuring styles for various ttk widgets such as frames, labels, buttons, entries, comboboxes, scrollbars, and progress bars. The styles include settings for background colors, foreground colors, border colors, fonts, padding, and state-specific appearances (e.g., active, pressed, disabled). The method ensures a consistent visual theme for the game view section of the GUI.
    def _setup_game_styles(self) -> None:
        self._game_palette = {
            "bg": "#f7f8fa",
            "surface": "#ffffff",
            "surface_soft": "#fbfbfc",
            "line": "#d9dde3",
            "text": "#1f2328",
            "muted": "#5b6573",
            "green": "#2fb34a",
            "green_dark": "#25933c",
            "green_soft": "#eaf8ee",
        }

        style = ttk.Style(cast(Any, self))
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        p = self._game_palette

        style.configure("Game.TFrame", background=p["bg"])
        style.configure("Game.TLabel", background=p["bg"], foreground=p["text"])

        style.configure(
            "Game.TLabelframe",
            background=p["bg"],
            bordercolor=p["line"],
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "Game.TLabelframe.Label",
            background=p["bg"],
            foreground=p["text"],
        )

        style.configure(
            "Game.TButton",
            background=p["surface"],
            foreground=p["text"],
            bordercolor=p["line"],
            lightcolor=p["surface"],
            darkcolor=p["surface"],
            relief="solid",
            borderwidth=1,
            padding=(8, 3),
        )
        style.map(
            "Game.TButton",
            background=[("active", p["surface_soft"]), ("pressed", "#eef1f4")],
            foreground=[("disabled", "#9aa3ad")],
        )

        style.configure(
            "Game.TEntry",
            fieldbackground=p["surface"],
            background=p["surface"],
            foreground=p["text"],
            bordercolor=p["line"],
            lightcolor=p["line"],
            darkcolor=p["line"],
            relief="solid",
            borderwidth=1,
            padding=(4, 3),
        )

        style.configure(
            "Game.TCombobox",
            fieldbackground=p["surface"],
            background=p["surface"],
            foreground=p["text"],
            bordercolor=p["line"],
            lightcolor=p["line"],
            darkcolor=p["line"],
            arrowsize=13,
            relief="solid",
            borderwidth=1,
            padding=(4, 3),
        )
        style.map(
            "Game.TCombobox",
            fieldbackground=[("readonly", p["surface"])],
            background=[("readonly", p["surface"])],
            foreground=[("readonly", p["text"])],
        )

        style.configure(
            "Game.Vertical.TScrollbar",
            background="#cfd6dd",
            troughcolor=p["surface"],
            bordercolor=p["surface"],
            arrowcolor="#5b6573",
            lightcolor=p["surface"],
            darkcolor=p["surface"],
            relief="flat",
            gripcount=0,
            width=11,
        )

        style.configure(
            "Game.Horizontal.TScrollbar",
            background="#cfd6dd",
            troughcolor=p["surface"],
            bordercolor=p["surface"],
            arrowcolor="#5b6573",
            lightcolor=p["surface"],
            darkcolor=p["surface"],
            relief="flat",
            gripcount=0,
            width=11,
        )

        style.configure(
            "Game.Horizontal.TProgressbar",
            background=p["green"],
            troughcolor="#ffffff",
            bordercolor=p["line"],
            lightcolor=p["green"],
            darkcolor=p["green_dark"],
            thickness=16,
        )

    # This method sets up the styles for the target picker section of the GUI, defining a color palette and configuring styles for various ttk widgets such as frames, labels, buttons, entries, and scrollbars. The styles include settings for background colors, foreground colors, border colors, fonts, padding, and state-specific appearances (e.g., active, pressed, disabled). The method ensures a consistent visual theme for the target picker section of the GUI.
    def _setup_target_picker_styles(self) -> None:
        gp = self._game_palette
        self._target_picker_palette = {
            "bg": gp["bg"],
            "surface": gp["surface"],
            "surface_soft": gp["surface_soft"],
            "line": gp["line"],
            "text": gp["text"],
            "muted": gp["muted"],
            "accent": gp["green"],
            "accent_dark": gp["green_dark"],
            "accent_soft": gp["green_soft"],
        }

        style = ttk.Style(cast(Any, self))
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        p = self._target_picker_palette

        style.configure("TargetPicker.TFrame", background=p["bg"])
        style.configure("TargetPicker.Surface.TFrame", background=p["surface"])
        style.configure("TargetPicker.TLabel", background=p["bg"], foreground=p["text"], font=("Segoe UI", 10))
        style.configure("TargetPicker.Muted.TLabel", background=p["bg"], foreground=p["muted"], font=("Segoe UI", 9))
        style.configure(
            "TargetPicker.Counter.TLabel",
            background=p["bg"],
            foreground=p["accent_dark"],
            font=("Segoe UI Semibold", 9),
        )
        style.configure(
            "TargetPicker.TButton",
            background=p["surface"],
            foreground=p["text"],
            bordercolor=p["line"],
            lightcolor=p["surface"],
            darkcolor=p["surface"],
            relief="solid",
            borderwidth=1,
            padding=(8, 4),
            font=("Segoe UI", 9),
        )
        style.map(
            "TargetPicker.TButton",
            background=[("active", p["surface_soft"]), ("pressed", "#eef1f4")],
            foreground=[("disabled", "#9aa3ad")],
        )
        style.configure(
            "TargetPicker.Primary.TButton",
            background=p["accent"],
            foreground="#ffffff",
            bordercolor=p["accent_dark"],
            lightcolor=p["accent"],
            darkcolor=p["accent"],
            relief="solid",
            borderwidth=1,
            padding=(9, 4),
            font=("Segoe UI Semibold", 9),
        )
        style.map(
            "TargetPicker.Primary.TButton",
            background=[("active", "#34be53"), ("pressed", p["accent_dark"]), ("disabled", "#9dc9a8")],
            foreground=[("disabled", "#f2f8f3")],
        )
        style.configure(
            "TargetPicker.TEntry",
            fieldbackground=p["surface"],
            background=p["surface"],
            foreground=p["text"],
            bordercolor=p["line"],
            lightcolor=p["line"],
            darkcolor=p["line"],
            relief="solid",
            borderwidth=1,
            padding=(4, 3),
        )
        style.configure(
            "TargetPicker.Vertical.TScrollbar",
            background="#cfd6dd",
            troughcolor=p["surface"],
            bordercolor=p["surface"],
            arrowcolor="#5b6573",
            lightcolor=p["surface"],
            darkcolor=p["surface"],
            relief="flat",
            gripcount=0,
            width=11,
        )

    # This method applies the target picker theme to a given Listbox widget. It configures the Listbox's background color, foreground color, selection background and foreground colors, highlight background and color, border width, and relief style based on the target picker palette defined in the `_setup_target_picker_styles` method. This ensures that the Listbox used in the target picker section of the GUI has a consistent visual appearance that matches the overall theme of the target picker.
    def _apply_target_picker_listbox_theme(self, lb: tk.Listbox) -> None:
        p = self._target_picker_palette
        lb.configure(
            bg=p["surface"],
            fg=p["text"],
            selectbackground=p["accent_soft"],
            selectforeground=p["text"],
            highlightbackground=p["line"],
            highlightcolor=p["line"],
            bd=1,
            relief="solid",
        )

    # This method applies the game theme to a given widget and all of its child widgets recursively. It checks the class of each widget and configures its styles based on the game palette defined in the `_setup_game_styles` method. The method handles various ttk widgets such as frames, labels, buttons, entries, comboboxes, scrollbars, and progress bars, as well as standard Tkinter widgets like Button, Listbox, and Text. It uses a try-except block to catch any `tk.TclError` exceptions that may occur during configuration (e.g., if a widget does not support certain options) and continues applying the theme to child widgets regardless of errors.
    def _apply_game_theme(self, widget: object) -> None:
        p = self._game_palette
        w = cast(Any, widget)
        cls = str(w.winfo_class())

        def cfg(target: object, **kwargs: object) -> None:
            cast(Any, target).configure(**kwargs)

        try:
            if cls == "TFrame":
                cfg(w, style="Game.TFrame")
            elif cls == "TLabel":
                cfg(w, style="Game.TLabel")
            elif cls == "TLabelframe":
                cfg(w, style="Game.TLabelframe")
            elif cls == "TButton":
                cfg(w, style="Game.TButton")
            elif cls == "TEntry":
                cfg(w, style="Game.TEntry")
            elif cls == "TCombobox":
                cfg(w, style="Game.TCombobox")
            elif cls == "TScrollbar":
                orient = str(w.cget("orient"))
                cfg(w, style="Game.Horizontal.TScrollbar" if orient == "horizontal" else "Game.Vertical.TScrollbar")
            elif cls == "TProgressbar":
                cfg(w, style="Game.Horizontal.TProgressbar")
            elif cls == "Button":
                cfg(
                    w,
                    bg=p["surface"],
                    fg=p["text"],
                    activebackground=p["surface_soft"],
                    activeforeground=p["text"],
                    relief="solid",
                    bd=1,
                    highlightthickness=0,
                )
            elif cls == "Listbox":
                cfg(
                    w,
                    bg=p["surface"],
                    fg=p["text"],
                    selectbackground=p["green_soft"],
                    selectforeground=p["text"],
                    highlightbackground=p["line"],
                    highlightcolor=p["line"],
                    bd=1,
                    relief="solid",
                )
            elif cls == "Text":
                cfg(
                    w,
                    bg=p["surface"],
                    fg=p["text"],
                    insertbackground=p["text"],
                    highlightbackground=p["line"],
                    highlightcolor=p["line"],
                    bd=1,
                    relief="solid",
                )
        except tk.TclError:
            pass

        for child in w.winfo_children():
            self._apply_game_theme(child)

    # This method centers a given Toplevel window on the screen based on the specified width and height. It first updates the window's idle tasks to ensure that the geometry information is up to date, then retrieves the screen width and height. It calculates the x and y coordinates needed to position the window in the center of the screen, ensuring that they are not negative. Finally, it sets the geometry of the window using the calculated dimensions and coordinates.
    def _center_toplevel(self, win: tk.Toplevel, width: int, height: int) -> None:
        win.update_idletasks()
        screen_w = win.winfo_screenwidth()
        screen_h = win.winfo_screenheight()
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2)
        win.geometry(f"{width}x{height}+{x}+{y}")
