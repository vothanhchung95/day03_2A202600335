from src.flashcard.storage import FlashcardStorage
from src.api.synonym_api import get_synonyms
from src.api.oxford_tool import oxford_define

# Initialize storage
storage = FlashcardStorage()

# --- Define execution functions (Functions) ---

def list_sets_func():
    try:
        sets = storage.list_sets()
        if not sets:
            return "No flashcard sets available yet."
        return "\n".join([f"- {s.name} ({len(s.cards)} cards)" for s in sets])
    except Exception as e:
        return f"Error: {str(e)}"

def create_set_func(set_name: str):
    try:
        storage.create_set(set_name)
        return f"Flashcard set '{set_name}' created successfully."
    except Exception as e:
        return f"Error: {str(e)}"

def add_card_func(set_name: str, front: str, back: str):
    try:
        # You can extend with synonyms if needed
        storage.add_card(set_name, front, back)
        return f"Added word '{front}' to set '{set_name}'."
    except Exception as e:
        return f"Error: {str(e)}"

def list_cards_func(set_name: str):
    try:
        cards = storage.list_cards(set_name)
        if not cards:
            return f"Set '{set_name}' is empty."
        return "\n".join([f"{c.front}: {c.back}" for c in cards])
    except Exception as e:
        return f"Error: {str(e)}"

# --- NEW: synonym tool function ---

def get_synonyms_func(word: str):
    try:
        synonyms = get_synonyms(word)
        if not synonyms:
            return f"No synonyms found for '{word}'."
        return ", ".join(synonyms)
    except Exception as e:
        return f"Error: {str(e)}"

def get_oxford_definition_func(word: str):
    try:
        definition = oxford_define(word)
        if not definition:
            return f"No official definition found for '{word}'."
        return definition
    except Exception as e:
        return f"Error calling Oxford API: {str(e)}"
# --- Tool definitions ---

tools = [
    {
        "name": "list_flashcard_sets",
        "description": "List all available flashcard sets.",
        "func": list_sets_func
    },
    {
        "name": "create_flashcard_set",
        "description": "Create a new flashcard set. Parameters: set_name (name of the set).",
        "func": create_set_func
    },
    {
        "name": "add_card_to_set",
        "description": "Add a new flashcard (word and meaning). Parameters: set_name, front (English), back (Vietnamese).",
        "func": add_card_func
    },
    {
        "name": "list_cards_in_set",
        "description": "View all cards in a flashcard set. Parameter: set_name.",
        "func": list_cards_func
    },
    {
        "name": "get_synonyms",
        "description": "Get synonyms for an English word. Parameter: word.",
        "func": get_synonyms_func
    },
    {
        "name": "get_oxford_definition",
        "description": "Get the official English definition and usage from Oxford Dictionary. Best for complex words or formal learning. Parameter: word.",
        "func": get_oxford_definition_func
    }
]