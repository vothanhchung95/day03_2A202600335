import time
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger


class Chatbot:
    """
    Baseline chatbot: stateful multi-turn conversation, no tools, no reasoning loop.
    Contrast this with ReActAgent to see the difference in capability.
    """

    SYSTEM_PROMPT = (
        "You are a helpful assistant. Answer the user's questions clearly and concisely."
    )

    def __init__(self, llm: LLMProvider):
        self.llm = llm
        self.history: List[Dict[str, str]] = []  # [{"role": "user"|"assistant", "content": "..."}]

    def chat(self, user_input: str) -> str:
        """Send a message and get a reply. History is maintained automatically."""
        self.history.append({"role": "user", "content": user_input})

        # Build a single prompt that includes conversation history
        prompt = self._build_prompt()

        logger.log_event("CHATBOT_TURN", {
            "model": self.llm.model_name,
            "turn": len(self.history),
            "input": user_input,
        })

        start = time.time()
        result = self.llm.generate(prompt, system_prompt=self.SYSTEM_PROMPT)
        latency = int((time.time() - start) * 1000)

        reply = result["content"]
        self.history.append({"role": "assistant", "content": reply})

        logger.log_event("CHATBOT_REPLY", {
            "latency_ms": latency,
            "tokens": result.get("usage", {}),
            "reply_preview": reply[:120],
        })

        return reply

    def reset(self):
        """Clear conversation history."""
        self.history = []
        logger.log_event("CHATBOT_RESET", {})

    def _build_prompt(self) -> str:
        """Flatten history into a plain-text prompt (works with all providers)."""
        lines = []
        for msg in self.history:
            role = "User" if msg["role"] == "user" else "Assistant"
            lines.append(f"{role}: {msg['content']}")
        lines.append("Assistant:")
        return "\n".join(lines)
