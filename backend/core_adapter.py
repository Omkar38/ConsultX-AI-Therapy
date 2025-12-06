# backend/core_adapter.py
from typing import Any, Dict, Optional

import os

try:  # Optional dependency; skip silently if missing.
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - optional helper
    load_dotenv = None

if load_dotenv:
    load_dotenv()


def _get_orchestrator():
    """
    Import orchestrator lazily so environments without heavy deps
    can still import this module (callers handle RuntimeError).
    """
    try:
        from backend.core import orchestrator as orch  # type: ignore
    except Exception as exc:  # pragma: no cover - surfaced to caller
        raise RuntimeError(f"ConsultX RAG pipeline unavailable: {exc}") from exc
    return orch

def run_therapy_turn(
    user_message: str,
    *,
    country_code: str = "US",
    history_summary: str = "",
    transcript_block: str = "",
    k: int = 2,
    model: str = "gemini-2.0-flash",
    session_id: Optional[str] = None,
    use_guardrails: bool = True,
) -> Dict[str, Any]:
    """
    Thin wrapper around core.orchestrator.run_generate_reply.

    This is the function your teammates (api/session_tracking/frontend/cli) should call.
    """

    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Put it in your environment or .env file."
        )

    orch = _get_orchestrator()
    out = orch.run_generate_reply(
        user_text=user_message,
        k=k,
        model=model,
        country_code=country_code,
        history_summary=history_summary,
        transcript_block=transcript_block,
        session_id=session_id,
        use_guardrails=use_guardrails,
    )

    # Expose only what the API/frontend/CLI needs; keep internals flexible
    return {
        # Main thing Jiyang cares about: AFTER guardrails
        "reply": out.get("reply", ""),
        # Optional raw model output
        "reply_raw": out.get("reply_raw", ""),
        # Safety metadata
        "risk": out.get("risk", {}),
        "guardrail_action": out.get("guardrail_action", "none"),
        "guardrail_notes": out.get("guardrail_notes", []),
        # Debug / observability
        "docs": out.get("docs", []),
        "prompt": out.get("prompt", ""),
        "session_id": session_id,
    }
