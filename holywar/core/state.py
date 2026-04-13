from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from holywar.data.models import CardDefinition


ATTACK_SLOTS = 3
DEFENSE_SLOTS = 3
ARTIFACT_SLOTS = 4
MAX_HAND = 8
TURN_INSPIRATION = 10


@dataclass(slots=True)
class CardInstance:
    uid: str
    definition: CardDefinition
    owner: int
    current_faith: int | None
    exhausted: bool = False
    blessed: list[str] = field(default_factory=list)
    cursed: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "uid": self.uid,
            "definition": self.definition.to_dict(),
            "owner": self.owner,
            "current_faith": self.current_faith,
            "exhausted": self.exhausted,
            "blessed": self.blessed,
            "cursed": self.cursed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CardInstance":
        return cls(
            uid=data["uid"],
            definition=CardDefinition.from_dict(data["definition"]),
            owner=data["owner"],
            current_faith=data.get("current_faith"),
            exhausted=bool(data.get("exhausted", False)),
            blessed=list(data.get("blessed", [])),
            cursed=list(data.get("cursed", [])),
        )


@dataclass(slots=True)
class PlayerState:
    name: str
    deck: list[str]
    white_deck: list[str]
    hand: list[str]
    graveyard: list[str]
    excommunicated: list[str]
    attack: list[str | None]
    defense: list[str | None]
    artifacts: list[str | None]
    building: str | None
    sin: int = 0
    inspiration: int = TURN_INSPIRATION

    @classmethod
    def empty(cls, name: str) -> "PlayerState":
        return cls(
            name=name,
            deck=[],
            white_deck=[],
            hand=[],
            graveyard=[],
            excommunicated=[],
            attack=[None] * ATTACK_SLOTS,
            defense=[None] * DEFENSE_SLOTS,
            artifacts=[None] * ARTIFACT_SLOTS,
            building=None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "deck": self.deck,
            "white_deck": self.white_deck,
            "hand": self.hand,
            "graveyard": self.graveyard,
            "excommunicated": self.excommunicated,
            "attack": self.attack,
            "defense": self.defense,
            "artifacts": self.artifacts,
            "building": self.building,
            "sin": self.sin,
            "inspiration": self.inspiration,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PlayerState":
        return cls(
            name=data["name"],
            deck=list(data["deck"]),
            white_deck=list(data["white_deck"]),
            hand=list(data["hand"]),
            graveyard=list(data["graveyard"]),
            excommunicated=list(data["excommunicated"]),
            attack=list(data["attack"]),
            defense=list(data["defense"]),
            artifacts=list(data["artifacts"]),
            building=data.get("building"),
            sin=int(data.get("sin", 0)),
            inspiration=int(data.get("inspiration", TURN_INSPIRATION)),
        )


@dataclass(slots=True)
class GameState:
    players: list[PlayerState]
    instances: dict[str, CardInstance]
    active_player: int
    turn_number: int
    phase: str = "preparation"
    preparation_turns_done: int = 0
    coin_toss_winner: int | None = None
    flags: dict[str, Any] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)
    winner: int | None = None

    def log(self, message: str) -> None:
        self.logs.append(message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "players": [p.to_dict() for p in self.players],
            "instances": {k: v.to_dict() for k, v in self.instances.items()},
            "active_player": self.active_player,
            "turn_number": self.turn_number,
            "phase": self.phase,
            "preparation_turns_done": self.preparation_turns_done,
            "coin_toss_winner": self.coin_toss_winner,
            "flags": self.flags,
            "logs": self.logs,
            "winner": self.winner,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameState":
        return cls(
            players=[PlayerState.from_dict(item) for item in data["players"]],
            instances={k: CardInstance.from_dict(v) for k, v in data["instances"].items()},
            active_player=int(data["active_player"]),
            turn_number=int(data["turn_number"]),
            phase=str(data.get("phase", "preparation")),
            preparation_turns_done=int(data.get("preparation_turns_done", 0)),
            coin_toss_winner=data.get("coin_toss_winner"),
            flags=dict(data.get("flags", {})),
            logs=list(data.get("logs", [])),
            winner=data.get("winner"),
        )

    def save(self, path: str | Path) -> Path:
        out = Path(path)
        out.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return out

    @classmethod
    def load(cls, path: str | Path) -> "GameState":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(data)
