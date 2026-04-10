"""
run.py — CLI runner for ShopBot.

This module contains the interactive loop that powers the terminal UI.
It is imported by ``main.py`` at the project root.
"""

from __future__ import annotations

from app.agent.agent import SupportAgent
from app.core.config import get_settings
from app.utils.conversation_logger import save_conversation
from app.utils.logger import setup_logging


BANNER = """
╔══════════════════════════════════════════════════╗
║         ShopBot — TechNest Support Agent         ║
║   Type your question below.  'quit' to exit.     ║
╚══════════════════════════════════════════════════╝
"""


def run_cli() -> None:
    """Start the interactive CLI session."""
    setup_logging()
    print(BANNER)

    try:
        settings = get_settings()
    except Exception as exc:
        print(f"[Config Error] {exc}")
        print("Make sure GROQ_API_KEY is set in your .env file.")
        return

    try:
        agent = SupportAgent(settings)
    except Exception as exc:
        print(f"[Init Error] {exc}")
        return

    history: list[dict] = []

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[Session ended]")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "bye"):
            print("ShopBot: Thanks for contacting TechNest support. Have a great day!")
            break

        history.append({"role": "user", "content": user_input})

        try:
            reply, history = agent.respond(history)
            print(f"\nShopBot: {reply}\n")
        except Exception as exc:
            print(f"\n[Agent error] {exc}\n")
            # Remove the failed user message so history stays clean
            history.pop()

    # ── Persist conversation to disk ─────────────────────────────────────
    if history:
        path = save_conversation(history)
        print(f"[Conversation saved to {path}]")


if __name__ == "__main__":
    run_cli()