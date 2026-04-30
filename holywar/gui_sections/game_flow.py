from __future__ import annotations
# pyright: reportAttributeAccessIssue=false

import json
import random
from typing import TYPE_CHECKING, Any
import tkinter as tk
from tkinter import filedialog, messagebox

from holywar.ai.simple_ai import choose_action
from holywar.core.engine import GameEngine
from holywar.data.deck_builder import available_premade_decks, get_premade_label

# This mixin class provides methods for managing the game flow in the GUI, including showing different screens (main menu, game screen, deck manager), handling the start of a new game, managing turn flow and AI actions, handling chain priority during card interactions, and providing options to save the game state and export logs. It interacts with the game engine to execute game actions based on user input and AI decisions, while also updating the GUI accordingly.
class GUIGameFlowMixin:
    """Turn flow, AI loop, chain priority and persistence actions."""

    if TYPE_CHECKING:
        def __getattr__(self, _name: str) -> Any: ...

    # Methods to switch between different GUI sections (main menu, game screen, deck manager) by packing and unpacking the respective frames, allowing the user to navigate through the different parts of the application seamlessly.
    def show_main_menu(self) -> None:
        self.game_screen.pack_forget()
        self.deck_manager_frame.pack_forget()
        self.main_menu_frame.pack(fill="both", expand=True)

    # Methods to display the game screen and deck manager by hiding the other sections and showing the relevant frame, as well as syncing the deck filter expansions and reloading user decks when showing the deck manager to ensure that the displayed information is up to date.
    def show_game_screen(self) -> None:
        self.main_menu_frame.pack_forget()
        self.deck_manager_frame.pack_forget()
        self.game_screen.pack(fill="both", expand=True)

    # Methods to display the deck manager screen, hiding the main menu and game screen, and ensuring that the deck filter expansions are synced and user decks are reloaded to reflect any changes or updates made to the decks, providing an up-to-date view of the available decks for the user to manage.
    def show_deck_manager(self) -> None:
        self.main_menu_frame.pack_forget()
        self.game_screen.pack_forget()
        self.deck_manager_frame.pack(fill="both", expand=True)
        self._sync_deck_filter_expansions()
        self._deck_manager_reload_user_decks()

    # This method updates the options for premade decks in the game setup screen based on the selected religions for player 1 and player 2. It builds a mapping of available premade decks for each religion, updates the dropdown options for selecting premade decks, and ensures that the currently selected premade deck is valid for the chosen religion, defaulting to "AUTO (test)" if the previously selected deck is no longer available.
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

    # This method initializes a new game based on the current settings selected in the game setup screen, including player names, selected premade decks, and game mode (AI or two-player). It creates a new game engine instance with the specified parameters, sets up the necessary callbacks for certain game actions, initializes the random number generator with the provided seed, and resets various state variables related to turn flow and chain interactions. Finally, it updates the status message and refreshes the GUI to reflect the new game state.
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
        self.engine.choose_auto_play_drawn_card = self._choose_auto_play_drawn_card
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

    # This method returns the index of the current human player based on the game state and mode. If the game engine is not initialized, it returns None. If a chain is active, it returns the index of the player with priority in the chain. If the game mode is AI, it assumes player 0 is human and returns 0. Otherwise, it returns the index of the active player from the game engine's state.
    def current_human_idx(self) -> int | None:
        if self.engine is None:
            return None
        if self.chain_active:
            return self.chain_priority_idx
        if self.mode_var.get() == "ai":
            return 0
        return self.engine.state.active_player

    # This method determines whether the human player can currently take actions based on the game state, mode, and whether a chain is active. It checks if the game engine is initialized and if there is a winner, then evaluates the conditions for chain interactions and AI turns to determine if the human player has the opportunity to act at the current moment in the game.
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

    # This method manages the flow of turns in the game, starting a new turn if necessary when the previous turn has ended and there is no winner. It also checks if the game mode is AI and if it's the AI's turn to act, in which case it initiates the AI turn by calling the appropriate method to start the AI's decision-making process.
    def begin_turn_if_needed(self) -> None:
        if self.engine is None or self.ai_running:
            return
        if not self.turn_started and self.engine.state.winner is None:
            self.engine.start_turn()
            self.turn_started = True
            self.refresh()
        if self.mode_var.get() == "ai" and self.engine and self.engine.state.active_player == 1 and not self.ai_running:
            self.start_ai_turn()

    # This method initiates the AI's turn by setting the appropriate flags and scheduling the first step of the AI's decision-making process after a short delay. It ensures that the AI's actions are executed in a way that allows for smooth integration with the GUI and provides a responsive experience for the user while the AI is processing its turn.
    def start_ai_turn(self) -> None:
        self.ai_running = True
        self._ai_steps = 0
        self.after(max(50, self.ai_delay_ms), self.ai_step)

    # This method represents a single step in the AI's decision-making process during its turn. It checks the game state to determine if the AI can continue acting, and if so, it uses the choose_action function to determine the next action for the AI to take. If the AI decides to pass or if it reaches a certain number of steps without taking an action, it ends the AI's turn. Otherwise, it continues scheduling further steps until the turn is complete.
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

    # This method enables or disables the chain interaction feature in the game, allowing players to respond to actions with quick plays. It updates the internal state to reflect whether chains are enabled and updates the status message accordingly to inform the player of the current state of chain interactions.
    def set_chain_enabled(self, enabled: bool) -> None:
        self.chain_enabled.set(enabled)
        self.status_var.set(f"Catena {'abilitata' if enabled else 'disabilitata'}.")

    # This method retrieves the indexes of cards in the player's hand that are considered "quick" cards, which can be played in response to certain actions during a chain. It checks the player's hand for cards that are of type "Benedizione", "Maledizione", or specifically named "Moribondo", and returns a list of their indexes in the hand for use in determining valid quick play options during chain interactions.
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

    # This method determines the default target for a quick play action based on the player's hand and the current game state. It checks the player's hand for quick cards and identifies valid targets on the board, such as attack or defense slots, artifacts, or buildings, prioritizing targets based on the card being played and the opponent's board state. This helps streamline the quick play process by suggesting a default target for the player when they choose to respond with a quick card during a chain interaction.
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

    # This method checks if the specified player index corresponds to an AI-controlled player based on the current game mode. It returns True if the game mode is set to "ai" and the player index is 1 (indicating the second player), which is typically designated as the AI opponent in a single-player game against AI. This helps determine whether certain actions or prompts should be handled automatically for the AI player or if user input is required for a human player.
    def _is_ai_player(self, player_idx: int) -> bool:
        return self.mode_var.get() == "ai" and player_idx == 1

    # This method handles the process of choosing a card from the graveyard to activate a battle survival effect when a card is defeated in battle. It checks if there are valid candidate cards in the graveyard, prompts the player to decide whether they want to activate the effect, and if so, allows them to select a card from the graveyard to use for the survival effect. If the player is an AI, it automatically selects the first valid card from the graveyard without prompting.
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

    # This method handles the process of choosing a slot for automatically playing a card drawn from the deck. It checks if there are valid slot options available, prompts the player to select a slot for placing the drawn card, and returns the chosen slot token. If the player is an AI, it automatically selects the first available slot without prompting.
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

    def _choose_auto_play_drawn_card(
        self,
        player_idx: int,
        source_uid: str,
    ) -> bool:
        if self.engine is None:
            return True

        if self._is_ai_player(player_idx):
            return True

        inst = self.engine.state.instances.get(source_uid)
        card_name = inst.definition.name if inst is not None else "questa carta"
        player_name = self.engine.state.players[player_idx].name
        return messagebox.askyesno(
            "Effetto di Nun",
            f"{player_name} ha pescato {card_name}.\n\n"
            "Vuoi evocarla subito grazie a Nun?",
        )

    # This method prompts the human player to decide whether they want to activate cards in response to an action during a chain interaction. It displays a yes/no dialog asking the player if they want to activate cards in the chain at that moment, and returns True if the player chooses to activate, or False if they choose to pass. This allows the player to make strategic decisions about when to respond with quick plays during chain interactions.
    def _prompt_human_chain_decision(self, player_idx: int) -> bool:
        if self.engine is None:
            return False
        p = self.engine.state.players[player_idx]
        return messagebox.askyesno("Catena", f"{p.name}, vuoi attivare carte in catena ora?")

    # This method registers a pass action for the current player in the chain interaction. It increments the count of consecutive passes, checks if the chain should end based on the number of passes, and if not, it switches the priority to the other player and refreshes the GUI. This is called when a player chooses to pass their opportunity to respond in a chain interaction, allowing the game to progress through the chain until it resolves or ends due to consecutive passes.
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

    # This method handles the priority of actions during a chain interaction. It checks if the chain is active and if the game engine is initialized, then determines which player has priority in the chain. If the player with priority is an AI, it automatically processes the AI's response to the chain. If the player with priority is human, it prompts
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

    # This method initiates a chain interaction when a player takes an action that can be responded to with quick plays. It checks if the game engine is initialized, if chains are enabled, and if a chain is not already active. It then determines the defender player index and checks if they have valid quick cards in hand. If all conditions are met, it activates the chain, sets the priority to the defender, resets the pass count, refreshes the GUI, and handles the chain priority to allow for responses from the players.
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

    # This method checks if the AI player has valid quick cards in hand and automatically plays one of them in response to a chain interaction if the AI has priority. It iterates through the AI player's hand for quick cards, determines a default target for each card, and attempts to play it as a quick response. If the AI successfully plays a card, it resets the chain pass count and priority, refreshes the GUI, and continues handling chain priority. If the AI chooses to pass or has no valid quick cards, it registers a pass for the AI in the chain.
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

    # This method ends the current chain interaction, resetting the relevant state variables and resuming the AI's turn if it was paused waiting for chain resolution. It sets the chain as inactive, resets the pass count, and if the AI was running and it's the AI's turn, it schedules the next step of the AI's decision-making process. Finally, it refreshes the GUI to reflect the end of the chain interaction.
    def end_chain(self) -> None:
        self.chain_active = False
        self.chain_pass_count = 0
        # Resume AI main turn if it was paused waiting for chain resolution.
        if self.engine and self.ai_running and self.engine.state.active_player == 1:
            self.after(max(50, self.ai_delay_ms), self.ai_step)
        self.refresh()

    # This method registers a pass action for the current player in the chain interaction when they choose to pass their opportunity to respond. It checks if a chain is active and if the game engine is initialized, then calls the internal method to register the pass for the current player, allowing the chain to progress based on the players' decisions to respond or pass during the interaction.
    def chain_ok(self) -> None:
        if not self.chain_active or self.engine is None:
            return
        self._register_chain_pass_current()

    # This method ends the current player's turn, ensuring that the game engine is initialized and that the AI is not currently running. It also checks if a chain is active, in which case it prompts the player to resolve the chain before ending the turn. If all conditions are met, it calls the game engine's method to end the turn, resets the turn state, refreshes the GUI, and begins the next turn if needed.
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

    # This method saves the current game state to a JSON file. It checks if the game engine is initialized, then prompts the user to choose a file location for saving the game. If a valid path is selected, it calls the game engine's save method to write the game state to the specified file and updates the status message to indicate that the game has been saved successfully.
    def save_game(self) -> None:
        if self.engine is None:
            return
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        self.engine.state.save(path)
        self.status_var.set(f"Partita salvata: {path}")

    # This method exports the game logs to a text file. It checks if the game engine is initialized, then prompts the user to choose a file location for exporting the logs. If a valid path is selected, it calls the game engine's method to export the logs to the specified file and updates the status message to indicate that the log has been exported successfully.
    def export_log(self) -> None:
        if self.engine is None:
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt")])
        if not path:
            return
        self.engine.export_logs(path)
        self.status_var.set(f"Log esportato: {path}")
