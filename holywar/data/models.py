from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CardDefinition:
    name: str
    card_type: str
    crosses: str
    faith: int | None
    strength: int | None
    effect_text: str
    expansion: str
    is_token: bool = False
    aliases: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CardDefinition":
        raw_aliases = data.get("aliases", [])
        aliases: list[str]
        if isinstance(raw_aliases, list):
            aliases = [str(x).strip() for x in raw_aliases if str(x).strip()]
        elif isinstance(raw_aliases, str):
            aliases = [p.strip() for p in raw_aliases.split(",") if p.strip()]
        else:
            aliases = []
        return cls(
            name=data["name"],
            card_type=data["card_type"],
            crosses=str(data.get("crosses", "")),
            faith=data.get("faith"),
            strength=data.get("strength"),
            effect_text=data.get("effect_text", ""),
            expansion=data.get("expansion", ""),
            is_token=bool(data.get("is_token", False)),
            aliases=aliases,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "card_type": self.card_type,
            "crosses": self.crosses,
            "faith": self.faith,
            "strength": self.strength,
            "effect_text": self.effect_text,
            "expansion": self.expansion,
            "is_token": self.is_token,
            "aliases": list(self.aliases),
        }
