# backend/therapy_cli.py
import argparse
import os

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - optional helper
    def load_dotenv():
        return None

from backend.core_adapter import run_therapy_turn


def main() -> int:
    load_dotenv()  # load GOOGLE_API_KEY etc. if .env is present

    if not os.getenv("GOOGLE_API_KEY"):
        print("ERROR: GOOGLE_API_KEY is not set. Put it in your environment or .env file.")
        return 1

    parser = argparse.ArgumentParser(
        description="ConsultX therapy CLI – calls the LLM pipeline with guardrails."
    )
    parser.add_argument(
        "message",
        nargs="*",
        help="User message text. If omitted, you will be prompted interactively.",
    )
    parser.add_argument(
        "-s",
        "--session-id",
        default="cli-session",
        help="Session ID for tracking / memory (default: cli-session).",
    )
    parser.add_argument(
        "-c",
        "--country-code",
        default="US",
        help="Country code for safety / routing (default: US).",
    )
    parser.add_argument(
        "-k",
        type=int,
        default=3,
        help="Number of retrieved docs for RAG (default: 3).",
    )
    parser.add_argument(
        "-m",
        "--model",
        default="gemini-2.0-flash",
        help="Model name to use (default: gemini-2.0-flash).",
    )
    parser.add_argument(
        "--no-guardrails",
        action="store_true",
        help="Disable guardrails (NOT recommended for production).",
    )

    args = parser.parse_args()

    if args.message:
        user_message = " ".join(args.message)
    else:
        user_message = input("You: ").strip()

    out = run_therapy_turn(
        user_message=user_message,
        country_code=args.country_code,
        k=args.k,
        model=args.model,
        session_id=args.session_id,
        use_guardrails=not args.no_guardrails,
    )

    # Main output: AFTER guardrails
    print("\n=== ASSISTANT (after guardrails) ===\n")
    print(out["reply"])

    # Optional debug / safety info for teammate
    print("\n--- Meta ---")
    print("Session ID:", out.get("session_id"))
    print("Risk:", out.get("risk"))
    print("Guardrail action:", out.get("guardrail_action"))
    notes = out.get("guardrail_notes") or []
    if notes:
        print("Guardrail notes:")
        for n in notes:
            print(" -", n)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
