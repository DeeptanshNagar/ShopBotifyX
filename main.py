"""
main.py — CLI entrypoint for ShopBot.

Run with:
    python main.py

Type 'exit' or 'quit' to end the session.
"""

from agent import SupportAgent


BANNER = """
╔══════════════════════════════════════════════╗
║        ShopBot — TechNest Support Agent      ║
║  Type your question below. 'quit' to exit.   ║
╚══════════════════════════════════════════════╝
"""


def main():
    print(BANNER)

    try:
        agent = SupportAgent()
    except EnvironmentError as e:
        print(f"[Error] {e}")
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
        except Exception as e:
            print(f"\n[Agent error] {e}\n")
            # Pop the failed user message so history stays clean
            history.pop()


if __name__ == "__main__":
    main()
