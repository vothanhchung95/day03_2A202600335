import os
from dotenv import load_dotenv
import requests

load_dotenv()

APP_ID = os.getenv("OXFORD_APP_ID")
APP_KEY = os.getenv("OXFORD_APP_KEY")


def oxford_define(word: str):
    url = f"https://od-api-sandbox.oxforddictionaries.com/api/v2/entries/en-gb/{word.lower()}"

    headers = {
        "app_id": APP_ID,
        "app_key": APP_KEY
    }

    res = requests.get(url, headers=headers)

    if res.status_code != 200:
        return f"API error: {res.status_code}"

    data = res.json()

    defs = []
    for r in data.get("results", []):
        for l in r.get("lexicalEntries", []):
            for e in l.get("entries", []):
                for s in e.get("senses", []):
                    defs.extend(s.get("definitions", []))

    return defs[0] if defs else "No definition found"


# if __name__ == "__main__":
#     word = input("Enter a word to define: ")
#     definition = oxford_define(word)
#     print(f"Definition of '{word}': {definition}")