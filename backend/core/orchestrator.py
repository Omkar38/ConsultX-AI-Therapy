# backend/core/orchestrator.py
"""
End-to-end orchestration with optional conversation memory.
user_text -> risk_types -> retrieval -> prompt -> Gemini -> guardrails
"""
from typing import Dict, Any, Optional, List, Tuple
import importlib
from collections import deque

from .prompt import build_prompt
from .llm_gateway import make_gemini
from .retrieval import retrieve_context
import backend.core.guardrails as guardrails
from backend.core.session_store import store as session_store
from .router import default_router
_router = default_router()



# ------- simple in-memory session store -------
_SESSIONS: Dict[str, Dict[str, Any]] = {}  # { session_id: {"summary": str, "turns": deque([(u,r), ...], maxlen)} }

def _session_get(session_id: str, max_turns: int = 6) -> Tuple[str, str]:
    """
    Returns (summary, transcript_block) for prompt conditioning.
    transcript_block is "User:/Therapist:" lines for the last few turns.
    """
    if not session_id or session_id not in _SESSIONS:
        return "", ""
    s = _SESSIONS[session_id]
    summary = s.get("summary", "")
    turns: deque = s.get("turns", deque(maxlen=max_turns))
    lines = []
    for u, r in list(turns)[-max_turns:]:
        if u: lines.append(f"User: {u}")
        if r: lines.append(f"Therapist: {r}")
    return summary, "\n".join(lines)

def _session_update(session_id: str, user_text: str, reply_text: str, max_turns: int = 6) -> None:
    if not session_id: return
    if session_id not in _SESSIONS:
        _SESSIONS[session_id] = {"summary": "", "turns": deque(maxlen=max_turns)}
    s = _SESSIONS[session_id]
    s["turns"].append((user_text, reply_text))
    # naive rolling summary (short & safe)
    if not s["summary"]:
        s["summary"] = f"Conversation started. Key themes emerging."
    if len(s["turns"]) >= 2:
        # keep this lightweight to avoid latency
        last_u, _ = s["turns"][-1]
        s["summary"] = (s["summary"][:300] + f" Latest concern: {last_u[:200]}").strip()[:500]

# ------- risk module loader -------
_RISK_MODULE_NAME = "backend.core.risk_types"

def _load_risk_module():
    try:
        return importlib.import_module(_RISK_MODULE_NAME)
    except Exception:
        return importlib.import_module("risk_types")

def _call_risk_fn(mod, user_text: str) -> Dict[str, Any]:
    for name in ("assess", "analyze", "analyze_text", "evaluate", "predict", "classify", "run"):
        if hasattr(mod, name):
            out = getattr(mod, name)(user_text)
            if isinstance(out, dict):
                return out
    raise RuntimeError("risk_types should expose one of: assess/analyze/analyze_text/evaluate/predict/classify/run")

def _normalize_risk(raw: Dict[str, Any]) -> Dict[str, Any]:
    dims = raw.get("dimensions") or raw.get("dimension") or []
    if isinstance(dims, str): dims = [dims]
    return {
        "tier": raw.get("tier", "OK"),
        "emotion": raw.get("emotion"),
        "dimensions": dims,
        "score": int(raw.get("score", 0)) if raw.get("score") is not None else 0,
        "confidence": raw.get("confidence", 0.0),
    }

# ------- public helpers -------
def run_retrieval_only(user_text: str, k: Optional[int] = None) -> Dict[str, Any]:
    risk_mod = _load_risk_module()
    raw = _call_risk_fn(risk_mod, user_text)
    risk = _normalize_risk(raw)

    ctx, docs = retrieve_context(user_text, risk, k_override=k)

    compact_docs: List[Dict[str, Any]] = []
    for d in docs:
        meta = d.metadata or {}
        compact_docs.append({
            "id": meta.get("id", ""),
            "tags": meta.get("tags", ""),
            "preview": (d.page_content or "").replace("\n", " ")[:140],
        })

    return {"risk": risk, "context": ctx, "docs": compact_docs}
# backend/core/orchestrator.py


def run_generate_reply(
    user_text: str,
    k: Optional[int] = None,
    model: str = "gemini-2.0-flash",
    country_code: str = "US",
    history_summary: Optional[str] = None,
    transcript_block: Optional[str] = None,
    session_id: Optional[str] = None,
    use_guardrails: bool = True,   # ← new flag
) -> Dict[str, Any]:
    """
    Full pipeline with either explicit history (history_summary/transcript_block) or
    implicit memory via session_id.
    """
    """
    Runs the full ConsultX pipeline (routing, retrieval, LLM, risk, guardrails).

    Returns a dict like:
      {
        "reply": str,                # final therapist-safe reply
        "reply_raw": str,            # raw LLM output (pre-guardrails)
        "risk": { ... },             # risk dict from risk_types.assess()
        "guardrail_action": str,     # "none" | "soften" | "crisis_override"
        "guardrail_notes": list[str],
        "docs": [ { "id":..., "tags":..., "preview":... }, ... ],
        "prompt": str,               # prompt sent to LLM (for debugging)
      }
    """
    # 0) pre-route
    route_label, route_score = _router.route(user_text)
    if route_label == "crisis":
        safe = guardrails.enforce(user_text, "", {"tier":"crisis"}, country_code=country_code)
        return {
            "risk": {"tier":"crisis","emotion":None,"dimensions":[],"score":1,"confidence":1.0},
            "prompt": "",
            "reply_raw": "",
            "reply": safe["final"],
            "guardrail_action": safe["action"],
            "guardrail_notes": "Pre-route crisis.",
            "docs": []
        }
    if route_label.startswith("deny"):
        # soft refusal but supportive
        msg = ("Therapist:\nI can’t help with that topic. I’m here to support how you’re feeling and "
            "explore next steps you’d consider. If you’d like, we can focus on what this brings up for you.")
        safe = guardrails.enforce(user_text, msg, {"tier":"OK"}, country_code=country_code)
        return {
            "risk": {"tier":"OK","emotion":None,"dimensions":[],"score":0,"confidence":0.9},
            "prompt": "",
            "reply_raw": msg,
            "reply": safe["final"],
            "guardrail_action": "soften",
            "guardrail_notes": f"Pre-route deny: {route_label} ({route_score:.2f})",
            "docs": []
        }

    # 1) risk
    risk_mod = _load_risk_module()
    raw = _call_risk_fn(risk_mod, user_text)
    risk = _normalize_risk(raw)

    # 1.5) crisis short-circuit
    if guardrails._is_suicidal_text(user_text) or risk.get("tier","OK").lower() == "crisis":
        safe = guardrails.enforce(user_text, "", risk, country_code=country_code)
        # update session with the crisis reply so the next turn has context
        _session_update(session_id, user_text, safe["final"]) if session_id else None
        return {
            "risk": risk, "prompt": "", "reply_raw": "",
            "reply": safe["final"],
            "guardrail_action": safe["action"],
            "guardrail_notes": safe["notes"],
            "docs": []
        }
    

    # 2) retrieval
    ctx, docs = retrieve_context(user_text, risk, k_override=k)


    history_summary = session_store.get_summary(session_id) if session_id else ""
    transcript_block = session_store.get_transcript_block(session_id, max_pairs=5) if session_id else ""
    prompt = build_prompt(
        user_text=user_text,
        risk=risk,
        retrieved_snippets=ctx,
        history_summary=history_summary,
        transcript_block=transcript_block,
    )


    # 5) LLM
    llm_call = make_gemini(model=model, temperature=0.2, max_output_tokens=450)
    reply_raw = llm_call(prompt)

    # post-route the model reply (safety belt)
    post_label, post_score = _router.route(reply_raw)
    if post_label.startswith("deny"):
        reply_raw = ("Therapist:\nI want to keep this space safe and supportive. I can’t provide guidance on that topic. "
                    "If you’d like, we can shift to how you’re feeling and pick one small step you’d consider.")
    # 6) Guardrails (one call, from the module)
    # safe = guardrails.enforce(user_text, reply_raw, risk, country_code=country_code, prev_reply=session_store.get_last_reply(session_id) if session_id else None)

    prev = session_store.get_last_reply(session_id) if session_id else None

    if use_guardrails:
        safe = guardrails.enforce(
            user_text=user_text,
            llm_reply=reply_raw,
            risk=risk,
            country_code=country_code,
            prev_reply=prev,
        )
        final_reply = safe["final"]
        guardrail_action = safe["action"]
        guardrail_notes = safe["notes"]
    else:
        # No guardrail rewrite – just pass through what Gemini said.
        safe = {"final": reply_raw, "action": "bypass", "notes": "guardrails_disabled"}
        final_reply = reply_raw
        guardrail_action = "bypass"
        guardrail_notes = "guardrails_disabled"



    # prev = session_store.get_last_reply(session_id) if session_id else None
    # safe = guardrails.enforce(
    #     user_text=user_text,
    #     llm_reply=reply_raw,
    #     risk=risk,
    #     country_code=country_code,
    #     prev_reply=prev,
    # )


    # 7) Update session memory
    # persist turn
    if session_id:
        session_store.append_turn(session_id, user_text, final_reply)
        # optionally update a simple rolling summary (plug in your own summarizer later)
        # session_store.set_summary(session_id, new_summary_text)
    


    # 8) compact docs
    compact_docs: List[Dict[str, Any]] = []
    for d in docs:
        meta = d.metadata or {}
        compact_docs.append({
            "id": meta.get("id", ""),
            "tags": meta.get("tags", ""),
            "preview": (d.page_content or "").replace("\n"," ")[:140]
        })

    return {
        "risk": risk,
        "prompt": prompt,
        "reply_raw": reply_raw,
        "reply": safe["final"],
        "guardrail_action": safe["action"],
        "guardrail_notes": safe["notes"],
        "docs": compact_docs
    }

