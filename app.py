import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

# ---------------------------------------------------------------------
# Make sure we can import `backend.*` when running as:
#   streamlit run backend/app.py
# ---------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]  # project root
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.core import orchestrator as orch  # type: ignore

# ---------------------------------------------------------------------
# Simple helpers for conversation memory
# ---------------------------------------------------------------------
def build_history_summary(messages: List[Dict[str, Any]], max_chars: int = 400) -> str:
    """
    Very light-weight summary:
    just concat user messages and trim.
    For demo/presentation only; you can later plug in your real memory.py.
    """
    user_texts = [m["content"] for m in messages if m.get("role") == "user"]
    if not user_texts:
        return ""
    joined = " | ".join(user_texts)
    if len(joined) > max_chars:
        joined = joined[-max_chars:]
    return f"Key concerns so far: {joined}"

def build_transcript_block(messages: List[Dict[str, Any]], max_turns: int = 6) -> str:
    """
    Build a short text transcript of the **previous** turns in:
      User: ...
      Therapist: ...
    style, to feed into the LLM.
    """
    lines: List[str] = []
    # Only last `max_turns` messages to keep prompt compact
    for msg in messages[-max_turns:]:
        role = msg.get("role")
        content = (msg.get("content") or "").strip()
        if not content:
            continue
        if role == "user":
            prefix = "User"
        else:
            prefix = "Therapist"
        lines.append(f"{prefix}: {content}")
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Streamlit page config
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="ConsultX – Therapy Companion",
    page_icon="💬",
    layout="centered",
)

st.title("💬 ConsultX – AI Therapy Companion")
st.caption(
    "Prototype demo – uses Motivational Interviewing style, risk detection, "
    "and safety guardrails. Not a replacement for professional care."
)

# ---------------------------------------------------------------------
# Session state: simple in-memory chat log
# ---------------------------------------------------------------------
if "messages" not in st.session_state:
    # Each message: {"role": "user" | "assistant", "content": str, "meta"?: {...}}
    st.session_state["messages"]: List[Dict[str, Any]] = []

DEFAULT_MODEL = "gemini-2.0-flash"

# ---------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------
with st.sidebar:
    st.subheader("Settings")

    country_code = st.selectbox(
        "Country (for safety resources)",
        options=["US", "IN", "UK", "CA", "AU", "Other"],
        index=0,
    )

    k_ctx = st.slider(
        "RAG: number of context chunks (k)",
        min_value=0,
        max_value=8,
        value=3,
        step=1,
        help="How many retrieved snippets to feed into the LLM.",
    )

    model_name = st.text_input(
        "Model name",
        value=DEFAULT_MODEL,
        help="Passed through to your llm_gateway; default is gemini-2.0-flash.",
    )

    st.markdown("---")
    st.markdown(
        "**Safety note:** If you are in immediate danger, please contact local "
        "emergency services or a trusted human. This app is only a prototype."
    )

# ---------------------------------------------------------------------
# Render existing messages
# ---------------------------------------------------------------------
for msg in st.session_state["messages"]:
    role = msg["role"]
    content = msg["content"]

    if role == "user":
        with st.chat_message("user", avatar="🧑"):
            st.markdown(content)
    else:
        with st.chat_message("assistant", avatar="🧠"):
            st.markdown(content)

            meta = msg.get("meta") or {}
            if meta:
                with st.expander("Safety & Guardrails (debug)", expanded=False):
                    st.json(meta)

# ---------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------
user_input = st.chat_input("Share what's on your mind...")

if user_input:
    user_msg = {
        "role": "user",
        "content": user_input.strip(),
    }

    # 1) Build history **before** adding the new user turn to the transcript
    #    so transcript_block only contains previous turns,
    #    just like your Jupyter examples.
    prev_messages: List[Dict[str, Any]] = list(st.session_state["messages"])

    transcript_block = build_transcript_block(prev_messages, max_turns=6)
    # For the summary we can include the new user message as well (optional)
    history_summary = build_history_summary(prev_messages + [user_msg], max_chars=400)

    # 2) Show user message in UI & store it
    st.session_state["messages"].append(user_msg)
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_msg["content"])

    # 3) Call ConsultX pipeline
    try:
        out: Dict[str, Any] = orch.run_generate_reply(
            user_msg["content"],
            k=k_ctx,
            model=model_name,
            country_code=country_code,
            history_summary=history_summary,
            transcript_block=transcript_block,
        )
    except Exception as e:
        with st.chat_message("assistant", avatar="🧠"):
            st.error(f"Error calling ConsultX pipeline: {e}")
    else:
        reply_text: str = (out.get("reply") or "").strip() or "_No reply generated._"

        meta = {
            "risk": out.get("risk"),
            "guardrail_action": out.get("guardrail_action"),
            "guardrail_notes": out.get("guardrail_notes"),
        }

        # 4) Render assistant message
        with st.chat_message("assistant", avatar="🧠"):
            st.markdown(reply_text)
            with st.expander("Safety & Guardrails (debug)", expanded=False):
                st.json(meta)

        # 5) Persist assistant message with metadata
        st.session_state["messages"].append(
            {
                "role": "assistant",
                "content": reply_text,
                "meta": meta,
            }
        )
