"""Interactive CLI for Flashcard CRUD operations."""
import sys
from src.flashcard.storage import FlashcardStorage

db = FlashcardStorage("data/flashcards.json")


def prompt(label: str) -> str:
    return input(f"  {label}: ").strip()


def pause():
    input("\n  [Press Enter to continue]")


# ─────────────────────────────────────────────
#  CardSet menu
# ─────────────────────────────────────────────

def cardset_list():
    sets = db.list_sets()
    if not sets:
        print("  (no card sets found)")
    else:
        for s in sets:
            print(f"  - {s.name}  ({len(s.cards)} cards)")

def cardset_create():
    name = prompt("Set name")
    try:
        db.create_set(name)
        print(f"  Created set '{name}'.")
    except ValueError as e:
        print(f"  Error: {e}")

def cardset_rename():
    old = prompt("Current set name")
    new = prompt("New set name")
    try:
        db.rename_set(old, new)
        print(f"  Renamed '{old}' -> '{new}'.")
    except (KeyError, ValueError) as e:
        print(f"  Error: {e}")

def cardset_delete():
    name = prompt("Set name to delete")
    confirm = prompt(f"Delete '{name}' and ALL its cards? (yes/no)")
    if confirm.lower() != "yes":
        print("  Cancelled.")
        return
    try:
        db.delete_set(name)
        print(f"  Deleted set '{name}'.")
    except KeyError as e:
        print(f"  Error: {e}")

def cardset_menu():
    actions = {
        "1": ("List all sets",   cardset_list),
        "2": ("Create set",      cardset_create),
        "3": ("Rename set",      cardset_rename),
        "4": ("Delete set",      cardset_delete),
        "0": ("Back",            None),
    }
    while True:
        print("\n=== Card Set ===")
        for key, (label, _) in actions.items():
            print(f"  [{key}] {label}")
        choice = input("Choose: ").strip()
        if choice == "0":
            break
        action = actions.get(choice)
        if action:
            print()
            action[1]()
            pause()
        else:
            print("  Invalid option.")


# ─────────────────────────────────────────────
#  Card menu
# ─────────────────────────────────────────────

def card_list():
    name = prompt("Set name")
    try:
        cards = db.list_cards(name)
        if not cards:
            print("  (no cards in this set)")
        else:
            print(f"\n  {'#':<4} {'Front':<20} {'Back':<25} Synonyms")
            print("  " + "-" * 65)
            for i, c in enumerate(cards, 1):
                syns = ", ".join(c.synonyms) if c.synonyms else "-"
                print(f"  {i:<4} {c.front:<20} {c.back:<25} {syns}")
    except KeyError as e:
        print(f"  Error: {e}")

def card_get():
    name = prompt("Set name")
    front = prompt("English word (front)")
    try:
        c = db.get_card(name, front)
        print(f"\n  Front   : {c.front}")
        print(f"  Back    : {c.back}")
        print(f"  Synonyms: {', '.join(c.synonyms) if c.synonyms else '-'}")
    except KeyError as e:
        print(f"  Error: {e}")

def card_add():
    name = prompt("Set name")
    front = prompt("English word (front)")
    back = prompt("Vietnamese meaning (back)")
    syns_raw = prompt("Synonyms (comma-separated, or leave blank)")
    synonyms = [s.strip() for s in syns_raw.split(",") if s.strip()] if syns_raw else []
    try:
        db.add_card(name, front, back, synonyms)
        print(f"  Added card '{front}' to set '{name}'.")
    except (KeyError, ValueError) as e:
        print(f"  Error: {e}")

def card_update():
    name = prompt("Set name")
    front = prompt("English word to update (front)")
    print("  Leave blank to keep current value.")
    new_front    = prompt("New English word (front)")   or None
    new_back     = prompt("New Vietnamese meaning (back)") or None
    syns_raw     = prompt("New synonyms (comma-separated, or leave blank)")
    new_synonyms = [s.strip() for s in syns_raw.split(",") if s.strip()] if syns_raw else None
    try:
        updated = db.update_card(name, front,
                                 new_back=new_back,
                                 new_synonyms=new_synonyms,
                                 new_front=new_front)
        print(f"  Updated: {updated.front} -> {updated.back}  |  synonyms: {updated.synonyms}")
    except (KeyError, ValueError) as e:
        print(f"  Error: {e}")

def card_delete():
    name = prompt("Set name")
    front = prompt("English word to delete (front)")
    try:
        db.delete_card(name, front)
        print(f"  Deleted card '{front}' from set '{name}'.")
    except KeyError as e:
        print(f"  Error: {e}")

def card_menu():
    actions = {
        "1": ("List cards in a set", card_list),
        "2": ("Get card details",    card_get),
        "3": ("Add card",            card_add),
        "4": ("Update card",         card_update),
        "5": ("Delete card",         card_delete),
        "0": ("Back",                None),
    }
    while True:
        print("\n=== Card ===")
        for key, (label, _) in actions.items():
            print(f"  [{key}] {label}")
        choice = input("Choose: ").strip()
        if choice == "0":
            break
        action = actions.get(choice)
        if action:
            print()
            action[1]()
            pause()
        else:
            print("  Invalid option.")


# ─────────────────────────────────────────────
#  Main menu
# ─────────────────────────────────────────────

def main():
    print("================================")
    print("   Flashcard Manager (CRUD)   ")
    print("================================")
    while True:
        print("\n=== Main Menu ===")
        print("  [1] Card Set")
        print("  [2] Card")
        print("  [0] Exit")
        choice = input("Choose: ").strip()
        if choice == "1":
            cardset_menu()
        elif choice == "2":
            card_menu()
        elif choice == "0":
            print("  Bye!")
            sys.exit(0)
        else:
            print("  Invalid option.")


if __name__ == "__main__":
    main()
