import json
import os
from typing import Dict, List
from src.flashcard.models import CardSet, Card


class FlashcardStorage:
    """Reads and writes the full flashcard database to/from a JSON file."""

    def __init__(self, filepath: str = "data/flashcards.json"):
        self.filepath = filepath
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        if not os.path.exists(filepath):
            self._write({})

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read(self) -> Dict[str, dict]:
        with open(self.filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: Dict[str, dict]) -> None:
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # CardSet CRUD
    # ------------------------------------------------------------------

    def list_sets(self) -> List[CardSet]:
        """Return all card sets."""
        data = self._read()
        return [CardSet.from_dict(v) for v in data.values()]

    def get_set(self, set_name: str) -> CardSet:
        """Return a single card set by name. Raises KeyError if not found."""
        data = self._read()
        if set_name not in data:
            raise KeyError(f"Card set '{set_name}' not found.")
        return CardSet.from_dict(data[set_name])

    def create_set(self, set_name: str) -> CardSet:
        """Create a new empty card set. Raises ValueError if name already exists."""
        data = self._read()
        if set_name in data:
            raise ValueError(f"Card set '{set_name}' already exists.")
        new_set = CardSet(name=set_name)
        data[set_name] = new_set.to_dict()
        self._write(data)
        return new_set

    def rename_set(self, set_name: str, new_name: str) -> CardSet:
        """Rename a card set. Raises KeyError if not found, ValueError if new name taken."""
        data = self._read()
        if set_name not in data:
            raise KeyError(f"Card set '{set_name}' not found.")
        if new_name in data:
            raise ValueError(f"Card set '{new_name}' already exists.")
        card_set = CardSet.from_dict(data.pop(set_name))
        card_set.name = new_name
        data[new_name] = card_set.to_dict()
        self._write(data)
        return card_set

    def delete_set(self, set_name: str) -> None:
        """Delete a card set and all its cards."""
        data = self._read()
        if set_name not in data:
            raise KeyError(f"Card set '{set_name}' not found.")
        del data[set_name]
        self._write(data)

    # ------------------------------------------------------------------
    # Card CRUD  (set_name required for all operations)
    # ------------------------------------------------------------------

    def list_cards(self, set_name: str) -> List[Card]:
        """Return all cards in a set."""
        return self.get_set(set_name).cards

    def get_card(self, set_name: str, front: str) -> Card:
        """Return a card by its front text. Raises KeyError if not found."""
        cards = self.list_cards(set_name)
        for card in cards:
            if card.front == front:
                return card
        raise KeyError(f"Card '{front}' not found in set '{set_name}'.")

    def add_card(self, set_name: str, front: str, back: str, synonyms: List[str] = None) -> Card:
        """Add a new card to a set. Raises ValueError if front already exists in the set."""
        data = self._read()
        if set_name not in data:
            raise KeyError(f"Card set '{set_name}' not found.")
        cards = data[set_name]["cards"]
        if any(c["front"] == front for c in cards):
            raise ValueError(f"Card '{front}' already exists in set '{set_name}'.")
        new_card = Card(front=front, back=back, synonyms=synonyms or [])
        cards.append(new_card.to_dict())
        self._write(data)
        return new_card

    def update_card(
        self,
        set_name: str,
        front: str,
        new_back: str = None,
        new_synonyms: List[str] = None,
        new_front: str = None,
    ) -> Card:
        """
        Update an existing card's fields. Only provided (non-None) fields are changed.
        Raises KeyError if the card or set is not found.
        """
        data = self._read()
        if set_name not in data:
            raise KeyError(f"Card set '{set_name}' not found.")
        cards = data[set_name]["cards"]
        for card_dict in cards:
            if card_dict["front"] == front:
                if new_back is not None:
                    card_dict["back"] = new_back
                if new_synonyms is not None:
                    card_dict["synonyms"] = new_synonyms
                if new_front is not None:
                    if any(c["front"] == new_front for c in cards if c is not card_dict):
                        raise ValueError(f"Card '{new_front}' already exists in set '{set_name}'.")
                    card_dict["front"] = new_front
                self._write(data)
                return Card.from_dict(card_dict)
        raise KeyError(f"Card '{front}' not found in set '{set_name}'.")

    def delete_card(self, set_name: str, front: str) -> None:
        """Remove a card from a set by its front text."""
        data = self._read()
        if set_name not in data:
            raise KeyError(f"Card set '{set_name}' not found.")
        original_len = len(data[set_name]["cards"])
        data[set_name]["cards"] = [
            c for c in data[set_name]["cards"] if c["front"] != front
        ]
        if len(data[set_name]["cards"]) == original_len:
            raise KeyError(f"Card '{front}' not found in set '{set_name}'.")
        self._write(data)
