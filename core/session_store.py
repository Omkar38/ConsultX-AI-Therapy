# backend/core/session_store.py
from __future__ import annotations
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, deque

# Simple in-memory store (per-process). Good enough for notebooks / dev.
# Each session_id maps to:
#   - turns: deque[(user_text, bot_reply)]
#   - summary: short running summary string

_MAX_TURNS = 50  # keep last N turns per session to bound memory

class _SessionStore:
    def __init__(self):
        self._turns: Dict[str, deque[Tuple[str, str]]] = defaultdict(lambda: deque(maxlen=_MAX_TURNS))
        self._summary: Dict[str, str] = {}

    # --- turns ---
    def append_turn(self, session_id: str, user_text: str, bot_reply: str) -> None:
        if not session_id:
            return
        self._turns[session_id].append((user_text, bot_reply))

    def append_reply(self, session_id: str, bot_reply: str) -> None:
        """If you already appended user_text elsewhere and just want to add reply,
        you can use this; otherwise use append_turn."""
        if not session_id:
            return
        # try to pair with last user turn if present
        if self._turns[session_id] and self._turns[session_id][-1][1] == "":
            u, _ = self._turns[session_id][-1]
            self._turns[session_id][-1] = (u, bot_reply)
        else:
            # fallback: store reply with empty user (not ideal)
            self._turns[session_id].append(("", bot_reply))

    def get_last_reply(self, session_id: str) -> Optional[str]:
        if not session_id or session_id not in self._turns or not self._turns[session_id]:
            return None
        return self._turns[session_id][-1][1] or None

    def get_transcript_block(self, session_id: str, max_pairs: int = 5) -> str:
        if not session_id or session_id not in self._turns:
            return ""
        pairs = list(self._turns[session_id])[-max_pairs:]
        lines: List[str] = []
        for u, b in pairs:
            if u:
                lines.append(f"User: {u}")
            if b:
                lines.append(f"Therapist: {b}")
        return "\n".join(lines)

    # --- summary (very simple; you can plug in your own summarizer) ---
    def get_summary(self, session_id: str) -> str:
        return self._summary.get(session_id, "")

    def set_summary(self, session_id: str, summary: str) -> None:
        if session_id:
            self._summary[session_id] = (summary or "").strip()

# singleton
store = _SessionStore()
