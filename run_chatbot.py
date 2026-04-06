"""
Chatbot baseline CLI — run this to test the chatbot interactively.

Usage:
    python run_chatbot.py                  # uses DEFAULT_PROVIDER from .env
    python run_chatbot.py --provider openai
    python run_chatbot.py --provider google
    python run_chatbot.py --provider local

Commands inside the chat:
    /reset   — clear conversation history and start over
    /history — print the full conversation so far
    /quit    — exit
"""

import os
import sys
import argparse
from dotenv import load_dotenv

load_dotenv()

# Make sure src/ is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.chatbot.chatbot import Chatbot


def build_provider(provider_name: str):
    if provider_name == "openai":
        from src.core.openai_provider import OpenAIProvider
        api_key = os.getenv("OPENAI_API_KEY")
        model   = os.getenv("DEFAULT_MODEL", "gpt-5-mini")
        return OpenAIProvider(model_name=model, api_key=api_key)

    elif provider_name == "google":
        from src.core.gemini_provider import GeminiProvider
        api_key = os.getenv("GEMINI_API_KEY")
        model   = os.getenv("DEFAULT_MODEL", "gemini-1.5-flash")
        return GeminiProvider(model_name=model, api_key=api_key)

    elif provider_name == "local":
        from src.core.local_provider import LocalProvider
        model_path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")
        return LocalProvider(model_path=model_path)

    else:
        raise ValueError(f"Unknown provider: {provider_name!r}. Choose openai | google | local")


def main():
    parser = argparse.ArgumentParser(description="Chatbot baseline")
    parser.add_argument(
        "--provider",
        default=os.getenv("DEFAULT_PROVIDER", "openai"),
        choices=["openai", "google", "local"],
        help="LLM provider to use",
    )
    args = parser.parse_args()

    print(f"\n=== Chatbot Baseline  [provider: {args.provider}] ===")
    print("Commands: /reset  /history  /quit\n")

    llm     = build_provider(args.provider)
    chatbot = Chatbot(llm)

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not user_input:
            continue

        if user_input == "/quit":
            print("Bye!")
            break

        if user_input == "/reset":
            chatbot.reset()
            print("[History cleared]\n")
            continue

        if user_input == "/history":
            if not chatbot.history:
                print("[No history yet]\n")
            else:
                for msg in chatbot.history:
                    role = "You" if msg["role"] == "user" else "Bot"
                    print(f"  {role}: {msg['content']}")
                print()
            continue

        try:
            reply = chatbot.chat(user_input)
            print(f"Bot: {reply}\n")
        except Exception as e:
            print(f"[Error] {e}\n")


if __name__ == "__main__":
    main()
