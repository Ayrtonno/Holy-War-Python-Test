from __future__ import annotations

from dataclasses import dataclass
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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CardDefinition":
        return cls(
            name=data["name"],
            card_type=data["card_type"],
            crosses=str(data.get("crosses", "")),
            faith=data.get("faith"),
            strength=data.get("strength"),
            effect_text=data.get("effect_text", ""),
            expansion=data.get("expansion", ""),
            is_token=bool(data.get("is_token", False)),
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
        }