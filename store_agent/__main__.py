import argparse
import json
import os
from pathlib import Path
import sys

from dotenv import load_dotenv
from groq import APIError, AuthenticationError, Groq, RateLimitError

from store_agent.agent import Agent


def main():
    parser = argparse.ArgumentParser(description="Chat with Empório da Música.")
    parser.add_argument("--message", help="Ask one question and exit.")
    parser.add_argument("--trace", action="store_true", help="Show tool names and token usage on stderr.")
    args = parser.parse_args()

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    if not os.getenv("GROQ_API_KEY"):
        parser.exit(1, "Set GROQ_API_KEY in .env before starting the chat.\n")
    client = Groq(max_retries=0, timeout=30)
    agent = Agent(client, model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"))

    if args.message is None:
        print("Empório da Música — type /exit to leave, /reset to start over.")
    try:
        while True:
            text = args.message if args.message is not None else input("You: ").strip()
            if text == "/exit":
                return 0
            if text == "/reset":
                agent.history.clear()
                print("Conversation cleared.")
                if args.message is not None:
                    return 0
                continue
            try:
                print(agent.reply(text))
            except RateLimitError as error:
                wait = error.response.headers.get("retry-after", "a little")
                print(f"Groq rate limit reached. Wait {wait} seconds before trying again.", file=sys.stderr)
                return 1
            except AuthenticationError:
                print("Groq rejected the API key. Check your local .env.", file=sys.stderr)
                return 1
            except APIError:
                print("Groq is unavailable or rejected the request. No automatic retry was made.", file=sys.stderr)
                return 1
            except (ValueError, RuntimeError) as error:
                print(str(error), file=sys.stderr)
                if args.message is not None:
                    return 1
            finally:
                if args.trace:
                    print(json.dumps({"tools": agent.calls, "requests": agent.requests, "tokens": agent.tokens}), file=sys.stderr)
            if args.message is not None:
                return 0
    except (EOFError, KeyboardInterrupt):
        print()
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
