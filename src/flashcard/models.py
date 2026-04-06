from dataclasses import dataclass, field
from typing import List


@dataclass
class Card:
    front: str          # English vocabulary
    back: str           # Vietnamese meaning
    synonyms: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "front": self.front,
            "back": self.back,
            "synonyms": self.synonyms,
        }

    @staticmethod
    def from_dict(data: dict) -> "Card":
        return Card(
            front=data["front"],
            back=data["back"],
            synonyms=data.get("synonyms", []),
        )


@dataclass
class CardSet:
    name: str
    cards: List[Card] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "cards": [c.to_dict() for c in self.cards],
        }

    @staticmethod
    def from_dict(data: dict) -> "CardSet":
        return CardSet(
            name=data["name"],
            cards=[Card.from_dict(c) for c in data.get("cards", [])],
        )
