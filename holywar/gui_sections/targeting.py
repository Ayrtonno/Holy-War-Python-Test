from __future__ import annotations
# pyright: reportAttributeAccessIssue=false

from typing import TYPE_CHECKING, Any, cast
import tkinter as tk
from tkinter import messagebox, ttk

from holywar.core.engine import GameEngine
from holywar.core.state import GameState
from holywar.effects.runtime import runtime_cards, _norm
from holywar.effects.card_scripts_loader import iter_card_scripts
from holywar.scripting_api import RuleEventContext

# This mixin class provides targeting and board-picker logic used by play and activate flows in the Holy War game. It includes methods for cloning the game engine state for simulation purposes, checking if certain actions (attack, activate, play) can be performed on specific targets, determining valid targets based on the game state, resolving widgets for highlighting potential targets on the board, and opening a target picker dialog for the user to select targets. The mixin relies on the game engine's state and card scripts to determine valid actions and targets, and it interacts with the GUI to provide visual feedback and selection options for the player.
class GUITargetingMixin:
    """Targeting and board-picker logic used by play/activate flows."""

    if TYPE_CHECKING:
        def __getattr__(self, _name: str) -> Any: ...

    # This attribute is used to store a snapshot of the game state for simulation purposes. It is initialized as None and is populated with a dictionary representation of the game state when the `_clone_engine` method is called for the first time. The snapshot allows for efficient cloning of the game engine state without needing to serialize and deserialize the entire state multiple times during targeting simulations.
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

    # This method checks if an attack action can be performed from a specified slot to a target slot for a given player index. It clones the game engine state using the `_clone_engine` method and simulates the attack action. The method returns True if the attack action is valid and effective (i.e., it does not result in an error message indicating an invalid target), and False otherwise.
    def _can_attack_target(self, player_idx: int, from_slot: int, target_slot: int | None) -> bool:
        sim = self._clone_engine()
        if sim is None:
            return False
        res = sim.attack(player_idx, from_slot, target_slot)
        return bool(res.ok and self._is_effective_result_message(res.message))

    # This method checks if an ability can be activated from a specified source to a target for a given player index. It clones the game engine state using the `_clone_engine` method and simulates the activation action. The method returns True if the activation action is valid and effective (i.e., it does not result in an error message indicating an invalid target), and False otherwise.
    def _can_activate_target(self, player_idx: int, source: str, target: str | None) -> bool:
        sim = self._clone_engine()
        if sim is None:
            return False
        res = sim.activate_ability(player_idx, source, target)
        return bool(res.ok and self._is_effective_result_message(res.message))

    # This method checks if a card can be played from a specified hand index to a target for a given player index. It clones the game engine state using the `_clone_engine` method and simulates the play action. The method returns True if the play action is valid and effective (i.e., it does not result in an error message indicating an invalid target), and False otherwise. The `quick` parameter allows for a faster simulation that may skip certain checks, which can be useful for quickly validating potential targets without needing a full simulation of the play action.
    def _can_play_target(self, player_idx: int, hand_idx: int, target: str | None, quick: bool = False) -> bool:
        sim = self._clone_engine()
        if sim is None:
            return False
        if quick:
            res = sim.quick_play(player_idx, hand_idx, target)
        else:
            res = sim.play_card(player_idx, hand_idx, target)
        return bool(res.ok and self._is_effective_result_message(res.message))

    # This method checks if a result message from a simulated action indicates an effective outcome (i.e., the action was successful and did not encounter an error related to invalid targets). It normalizes the message text and checks for the presence of certain keywords that typically indicate an ineffective result, such as "no target", "invalid target", "unavailable", "impossible", etc. If any of these markers are found in the message, the method returns False, indicating that the result is not effective. Otherwise, it returns True.
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

    # This method returns a list of candidate tokens that can be used for targeting on the board. The tokens represent different slots and positions on the game board, such as attack slots (a1, a2, a3), defense slots (d1, d2, d3), artifact slots (r1, r2, r3, r4), and the building slot (b). These tokens are used in various targeting methods to identify potential targets for actions like attacks, activations, and plays.
    def _candidate_slot_tokens(self) -> list[str]:
        return ["a1", "a2", "a3", "d1", "d2", "d3", "r1", "r2", "r3", "r4", "b"]

    # This method splits a board token into its side and base components. The token is expected to be in the format "side:base", where "side" indicates whether the token refers to the player's own side ("own") or the opponent's side ("enemy"), and "base" indicates the specific slot or position on the board (e.g., "a1", "d2", "r3", "b"). If the token does not contain a colon, it is treated as having no explicit side, and the method returns (None, token). If the side component is recognized as one of several keywords indicating "own" or "enemy", it is normalized accordingly. Otherwise, the method returns (None, raw), treating the entire token as the base without an explicit side.
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

    # This method retrieves the card script associated with a given card instance identified by its UID. It checks if the game engine is initialized and if the specified UID corresponds to a valid card instance in the game state. If both conditions are met, it retrieves the card's definition name and looks up the corresponding script in the runtime cards registry. The method returns the card script if found, or None if the engine is not initialized or if the UID does not correspond to a valid card instance.
    def _card_script(self, uid: str):
        if self.engine is None:
            return None
        card_name = self.engine.state.instances[uid].definition.name
        return runtime_cards.get_script(card_name)

    # This method retrieves the raw card script specification for a given card instance identified by its UID. It checks if the game engine is initialized and if the specified UID corresponds to a valid card instance in the game state. If both conditions are met, it retrieves the card's definition name and looks up the corresponding raw script specification in the registry of card scripts. The method returns the raw script specification as a dictionary if found, or an empty dictionary if the engine is not initialized, if the UID does not correspond to a valid card instance, or if no matching script specification is found.
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

    # This method retrieves a list of manual targeting specifications for the "on play" actions of a card identified by its UID. It checks the raw card script for the specified UID and iterates through the "on_play_actions" defined in the script. For each action, it checks if it has a "target" field and if the corresponding action specification in the card script has a condition that evaluates to True in the current game context. If both conditions are met, it checks if the target specification requires manual selection based on certain fields (e.g., zone, card_filter, min_targets, etc.) and if the target type is "selected_target" or "selected_targets". If these criteria are satisfied, it adds the action index and target specification to the output list. The method returns a list of tuples containing the action index and target specification for each manual targeting action found.
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

    # This method retrieves the first manual targeting specification for the "on activate" actions of a card identified by its UID. It checks the raw card script for the specified UID and iterates through the "on_activate_actions" defined in the script. For each action, it checks if it has a "target" field and if the corresponding action specification in the card script has a condition that evaluates to True in the current game context. If both conditions are met, it checks if the target specification requires manual selection based on certain fields (e.g., zone, card_filter, min_targets, etc.) and if the target type is "selected_target" or "selected_targets". If these criteria are satisfied, it returns the target specification for the first manual targeting action found. If no such action is found, it returns None.
    def _first_play_target_spec(self, uid: str):
        actions = self._manual_play_target_actions(uid)
        if not actions:
            return None
        return actions[0][1]

    # This method retrieves the first manual targeting specification for the "on activate" actions of a card identified by its UID. It checks the raw card script for the specified UID and iterates through the "on_activate_actions" defined in the script. For each action, it checks if it has a "target" field and if the corresponding action specification in the card script has a condition that evaluates to True in the current game context. If both conditions are met, it checks if the target specification requires manual selection based on certain fields (e.g., zone, card_filter, min_targets, etc.) and if the target type is "selected_target" or "selected_targets". If these criteria are satisfied, it returns the target specification for the first manual targeting action found. If no such action is found, it returns None.
    def _play_targeting_mode(self, uid: str) -> str:
        script = self._card_script(uid)
        if script is None:
            return "auto"
        return str(script.play_targeting or "auto").strip().lower() or "auto"

    # This method retrieves the targeting mode for the "on activate" actions of a card identified by its UID. It checks the card script for the specified UID and returns the value of the "activate_targeting" field, which indicates the targeting mode to be used when activating abilities of that card. If the card script is not found or if the "activate_targeting" field is not defined, it defaults to returning "auto". The targeting mode can influence how valid targets are determined and how the target picker dialog is presented to the user during activation.
    def _activate_targeting_mode(self, uid: str) -> str:
        script = self._card_script(uid)
        if script is None:
            return "auto"
        return str(script.activate_targeting or "auto").strip().lower() or "auto"

    # This method retrieves a list of candidate tokens for guided targeting based on the "on play" actions of a card identified by its UID. It checks the raw card script for the specified UID and iterates through the "on_play_actions" defined in the script. For each action, it checks if it has a "target" field and if the corresponding action specification in the card script has a condition that evaluates to True in the current game context. If both conditions are met, it checks if the target specification is of type "selected_target" or "selected_targets". If so, it adds the candidate tokens derived from the target specification to the output list. The method returns a list of candidate tokens that can be used for guided targeting when playing the card.
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

    # This method retrieves a list of candidate tokens for guided targeting based on the "on activate" actions of a card identified by its UID. It checks the raw card script for the specified UID and iterates through the "on_activate_actions" defined in the script. For each action, it checks if it has a "target" field and if the corresponding action specification in the card script has a condition that evaluates to True in the current game context. If both conditions are met, it checks if the target specification is of type "selected_target" or "selected_targets". If so, it adds the candidate tokens derived from the target specification to the output list. The method returns a list of candidate tokens that can be used for guided targeting when activating abilities of the card.
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

    # This method retrieves a list of valid attack target tokens for a given player index and source slot. It checks each potential target slot (including None for direct attacks) to see if an attack action can be performed from the source slot to that target slot using the `_can_attack_target` method. If an attack is valid for a target slot, it adds the corresponding token (e.g., "a1", "d2", "r3", "b") or None to the output list. The method returns a list of valid attack target tokens that the player can choose from when performing an attack action.
    def _valid_attack_targets(self, player_idx: int, from_slot: int) -> list[int | None]:
        out: list[int | None] = []
        if self.engine is not None:
            opponent = self.engine.state.players[1 - player_idx]
            has_enemy_saints_on_field = any(uid is not None for uid in (opponent.attack + opponent.defense))
            if not has_enemy_saints_on_field:
                if self._can_attack_target(player_idx, from_slot, None):
                    out.append(None)
                return out
        if self._can_attack_target(player_idx, from_slot, None):
            out.append(None)
        for slot in range(3):
            if self._can_attack_target(player_idx, from_slot, slot):
                out.append(slot)
        return out

    # This method retrieves a list of valid activation target tokens for a given player index, source, and card UID. It first determines the targeting mode for the card's activation based on its script. Depending on the targeting mode (e.g., "board_card", "auto", "guided", "manual"), it retrieves a list of candidate tokens that can be targeted for activation. It then checks each candidate token using the `_can_activate_target` method to determine if it is a valid target for activation. If a candidate token is valid, it is added to the output list. The method returns a list of valid activation target tokens that the player can choose from when activating an ability of the card.
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

    # This method checks if there are any valid activation targets available for a given player index and source. It first checks if the game engine is initialized and if the specified source can be resolved to a valid card instance UID. If both conditions are met, it retrieves the card script for the corresponding UID and checks if the activation mode is one that requires manual targeting (e.g., "scripted", "custom") and if there are defined activation actions in the script. If these criteria are satisfied, it then checks if there is a valid activation target using the `_can_activate_target` method or if there are any valid activation targets returned by the `_valid_activation_targets` method. If either of these checks returns True, it indicates that there is at least one valid activation target available, and the method returns True. Otherwise, it returns False.
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

    # This method checks if there are any valid play targets available for a given player index, hand index, and card UID. It first checks if the game engine is initialized and if the specified UID corresponds to a valid card instance in the game state. If both conditions are met, it retrieves the card script for the corresponding UID and checks if the play targeting mode is one that requires manual targeting (e.g., "scripted", "custom") and if there are defined on-play actions in the script. If these criteria are satisfied, it then checks if there is a valid play target using the `_can_play_target` method or if there are any valid play targets returned by the `_valid_play_targets` method. If either of these checks returns True, it indicates that there is at least one valid play target available, and the method returns True. Otherwise, it returns False.
    def _clear_slot_highlights(self) -> None:
        for widget, old in self._slot_highlights:
            try:
                widget.configure(**old)
            except tk.TclError:
                pass
        self._slot_highlights.clear()
        apply_blocked = getattr(self, "_apply_blocked_artifact_slot_highlights", None)
        if callable(apply_blocked):
            apply_blocked()

    # This method checks if a given token corresponds to a valid board token that can be targeted for actions such as attacks or activations. It uses the `_split_board_token` method to parse the token and then checks if the base component of the token matches known patterns for attack slots (a1, a2, a3), defense slots (d1, d2, d3), artifact slots (r1, r2, r3, r4), or the building slot (b). The method returns True if the token is recognized as a valid board token, and False otherwise.
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

    # This method retrieves hints for card targeting based on the card's UID. It checks the play targeting mode for the specified UID and returns a tuple of two boolean values indicating whether the card can target the player's own saint (True/False) and whether it can target the opponent's saint (True/False). The method also checks for manual targeting specifications in the card's script and determines if the target zones include the field and if the owner of the target is specified as "me", "opponent", or "any". Based on these checks, it sets the appropriate hints for targeting. If no specific targeting information is found, it defaults to returning (False, False).
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

    # This method resolves a given token to a specific widget on the game board that can be highlighted as a potential target for actions such as attacks or activations. It takes into account the player's own index, an optional side hint (indicating whether to prioritize the player's own side or the opponent's side), and an optional card UID for additional targeting hints. The method checks if the token corresponds to a valid board token and then determines which widget on the board it refers to based on the current game state and the specified hints. If a valid widget is found for the token, it is returned; otherwise, the method returns None.
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

    # This method highlights the widgets corresponding to the specified target tokens on the game board. It first clears any existing highlights and then iterates through the list of target tokens. For each token, it resolves the corresponding widget using the `_resolve_highlight_widget` method, taking into account the player's own index, an optional side hint, and an optional card UID for additional targeting hints. If a valid widget is found for a token, it applies a visual highlight to indicate that it is a potential target. The method also keeps track of the original configuration of each highlighted widget so that it can be restored later when the highlights are cleared.
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

    # This method opens a target picker dialog for the player to select targets on the game board. It takes various parameters to customize the behavior of the target picker, such as the title and prompt text, candidate tokens for targeting, whether multiple targets can be selected, limits on the number of targets, whether manual input is allowed, and hints for targeting based on a card UID. The method creates a modal dialog with a list of candidate targets and allows the player to select from them or enter a manual target if allowed. It returns a tuple indicating whether the selection was confirmed (True/False) and the selected target token (or None if no selection was made).
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

        # If choices are not provided, generate them from the candidate tokens. Each choice is a tuple of (label, token), where the label is a user-friendly description of the token and the token is the actual identifier used for targeting. The `_format_guided_candidate` method is used to create the label for each candidate token. If choices are provided, they are normalized by stripping whitespace and removing duplicates while preserving order. Tokens that are empty or have already been seen are skipped during normalization.
        if choices is None:
            choices = []
            for token in (candidates or []):
                choices.append((self._format_guided_candidate(token, own_idx), token))

        # Normalize choices by stripping whitespace and removing duplicates while preserving order. This ensures that the list of choices presented to the player is clean and does not contain redundant entries. The normalized choices are stored in a new list, and a set is used to track seen tokens to efficiently skip duplicates.
        normalized_choices: list[tuple[str, str]] = []
        seen_tokens: set[str] = set()
        for label, token in choices:
            token = str(token).strip()
            if not token or token in seen_tokens:
                continue
            normalized_choices.append((label, token))
            seen_tokens.add(token)

        # If there are no valid choices and manual input is not allowed and selecting none is not allowed, then there is nothing to select and the method can return immediately with a successful result but no selection.
        if not normalized_choices and not allow_manual and not allow_none:
            return (True, None)

        # Extract the list of tokens from the normalized choices and determine which ones correspond to valid board tokens that can be highlighted. This is done by iterating through the normalized choices and using the `_resolve_highlight_widget` method to check if each token can be resolved to a valid widget on the board. Tokens that can be resolved are added to the list of `board_tokens`, which will be highlighted in the target picker dialog to indicate that they are valid targets.
        board_tokens: list[str] = []
        for _label, token in normalized_choices:
            if self._resolve_highlight_widget(token, own_idx=own_idx, side_hint=side_hint, card_uid=card_uid) is not None:
                board_tokens.append(token)
        
        # Initialize the list of selected tokens and the result dictionary.
        selected_tokens: list[str] = []
        result: dict[str, str | None] = {"value": ""}
        bindings: list[tuple[tk.Widget, str]] = []

        # Create a new top-level window for the target picker dialog. The window is configured with the specified title and centered on the screen with a fixed size. It is set as transient to the main application window to ensure it behaves as a modal dialog. The background color of the window is set according to the target picker palette defined in the application's theme.
        win = tk.Toplevel(cast(Any, self))
        win.title(title)
        self._center_toplevel(win, 700, 560)
        win.transient(cast(Any, self))
        p = self._target_picker_palette
        win.configure(bg=p["bg"])

        container = ttk.Frame(win, style="TargetPicker.TFrame", padding=(10, 10))
        container.pack(fill="both", expand=True)

        ttk.Label(container, text=prompt, wraplength=660, style="TargetPicker.TLabel").pack(anchor="w", pady=(0, 4))

        # Display instructions for selecting targets, which may vary depending on whether multiple selection is allowed and if there are limits on the number of targets. If multiple selection is allowed, the instructions will indicate how many targets can be selected, and if there are specific minimum or maximum limits, those will be included in the instructions as well. If multiple selection is not allowed, the instructions will simply indicate that the player can select from the list or by clicking on the field.
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

        # If manual input is allowed, create an entry field for the player to enter a manual target. The value entered in this field will be considered as a valid selection if it is not empty, regardless of the selections made in the listbox. This allows for flexibility in targeting, enabling players to specify targets that may not be listed as candidates or to use custom tokens that are not recognized by the automatic highlighting system.
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

        # If selecting none is allowed, add a button for "Senza Target" (Without Target) that allows the player to confirm their selection without choosing any targets. This provides an option for players who may want to activate an ability or perform an action that does not require a target, or who may want to skip targeting altogether.
        def _selection_ok() -> bool:
            raw_manual = manual_var.get().strip() if allow_manual else ""
            if raw_manual:
                return True
            count = len(selected_tokens)
            upper = max_targets if max_targets is not None else (9999 if allow_multi else 1)
            return min_targets <= count <= upper

        # This function synchronizes the selection in the listbox with the current list of selected tokens. It clears the current selection in the listbox and then iterates through the selected tokens, using the `token_to_index` mapping to find the corresponding index in the listbox for each token. If an index is found, it sets that index as selected in the listbox. This ensures that the visual representation of the selection in the listbox accurately reflects the internal state of which tokens are currently selected.
        def _sync_listbox() -> None:
            lb.selection_clear(0, tk.END)
            for token in selected_tokens:
                idx = token_to_index.get(token)
                if idx is not None:
                    lb.selection_set(idx)

        # This function refreshes the state of the target picker dialog, updating the counter of selected targets, the display of selected targets, the highlights on the board for valid targets, and the enabled/disabled state of the OK button based on whether the current selection is valid according to the specified criteria (e.g., minimum and maximum number of targets). It constructs a user-friendly message indicating how many targets are currently selected and what the limits are, and it updates the display accordingly. It also calls `_set_slot_highlights` to visually indicate which tokens on the board are currently selected as targets.
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

        # This function handles the logic for toggling the selection of a token when it is clicked on the board. If multiple selection is allowed, clicking a token will add it to the selection if it is not already selected, or remove it from the selection if it is already selected. If multiple selection is not allowed, clicking a token will set it as the only selected token, or clear the selection if it is already selected. After updating the selection based on the click, it calls `_refresh_state` to update the display and state of the target picker dialog accordingly.
        def _set_single(token: str) -> None:
            selected_tokens.clear()
            selected_tokens.append(token)
            _refresh_state()

        # This function is called when a token on the board is clicked. It toggles the selection of the token based on whether multiple selection is allowed and updates the list of selected tokens accordingly. If multiple selection is allowed, it adds or removes the token from the selection. If multiple selection is not allowed, it sets the token as the only selected token or clears the selection if it was already selected. After updating the selection, it calls `_refresh_state` to update the visual state of the target picker dialog.
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

        # This function is called when the selection in the listbox changes. It retrieves the currently selected indices from the listbox and maps them to the corresponding tokens using the `normalized_choices` list. It then updates the list of selected tokens based on the new selection, taking into account whether multiple selection is allowed and whether the order of selection should be preserved. If multiple selection is allowed and order preservation is enabled, it maintains the order of previously selected tokens while adding new selections in the order they appear in the listbox. After updating the selection, it calls `_refresh_state` to update the visual state of the target picker dialog.
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

        # Bind click events to the widgets corresponding to the board tokens so that clicking on them will toggle their selection in the target picker dialog. The `_toggle_token` function is called when a token widget is clicked, and it updates the selection state accordingly. The bindings are stored in a list so that they can be cleaned up later when the dialog is closed.
        for token in board_tokens:
            widget = self._resolve_highlight_widget(token, own_idx=own_idx, side_hint=side_hint, card_uid=card_uid)
            if widget is None:
                continue
            func_id = widget.bind("<Button-1>", lambda e, t=token: _toggle_token(t), add="+")
            bindings.append((widget, func_id))

        # This function is responsible for cleaning up the event bindings and highlights when the target picker dialog is closed. It iterates through the list of bindings and attempts to unbind the click events from the corresponding widgets. It also calls `_clear_slot_highlights` to remove any visual highlights from the board tokens that were highlighted during the target selection process. This ensures that the game board returns to its normal state after the target picker dialog is closed.
        def _cleanup() -> None:
            for widget, func_id in bindings:
                try:
                    widget.unbind("<Button-1>", func_id)
                except tk.TclError:
                    pass
            self._clear_slot_highlights()

        # This function is called when the OK button is clicked in the target picker dialog. It first checks if there is a valid manual input if manual input is allowed. If there is a valid manual input, it sets the result value to the manual input and closes the dialog. If there is no valid manual input, it checks if the current selection of tokens is valid according to the specified criteria (e.g., minimum and maximum number of targets). If the selection is not valid, it shows a warning message to the user indicating what the requirements are for a valid selection. If the selection is valid, it sets the result value to a comma-separated string of the selected tokens (or None if no tokens are selected and allow_none is True), cleans up the bindings and highlights, and closes the dialog.
        def _ok() -> None:
            raw_manual = manual_var.get().strip() if allow_manual else ""
            if raw_manual:
                result["value"] = raw_manual
                _cleanup()
                win.destroy()
                return

            # Validate the selection of tokens based on the specified criteria. If the selection is not valid, show a warning message to the user indicating what the requirements are for a valid selection. The message will vary depending on whether there are specific limits on the number of targets and whether multiple selection is allowed. If the selection is valid, proceed to set the result value and close the dialog.
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

        # This function is called when the "Senza Target" (Without Target) button is clicked, if selecting none is allowed. It sets the result value to None to indicate that no target was selected, cleans up the bindings and highlights, and closes the dialog. This provides a way for the player to confirm their choice of not selecting any targets.
        def _no_target() -> None:
            result["value"] = None
            _cleanup()
            win.destroy()

        # This function is called when the dialog is closed without confirming a selection (e.g., by clicking the close button on the window). It sets the result value to an empty string to indicate that no valid selection was made, cleans up the bindings and highlights, and closes the dialog. This ensures that if the player exits the target picker without making a valid selection, the method will return a consistent result indicating that no selection was made.
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
