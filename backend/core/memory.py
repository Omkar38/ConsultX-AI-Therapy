# backend/core/memory.py
from typing import Dict, List, Tuple
from .schemas import SessionState, ChatMessage

class SessionMemory:
    def __init__(self, max_window:int=8, max_summary_chars:int=800):
        self._sessions: Dict[str, SessionState] = {}
        self.max_window = max_window
        self.max_summary_chars = max_summary_chars

    def get_or_create(self, session_id:str) -> SessionState:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionState(session_id=session_id)
        return self._sessions[session_id]

    def add_user(self, session_id:str, text:str):
        s = self.get_or_create(session_id)
        s.messages.append(ChatMessage(role="user", content=text))
        self._trim(s)

    def add_assistant(self, session_id:str, text:str):
        s = self.get_or_create(session_id)
        s.messages.append(ChatMessage(role="assistant", content=text))
        self._trim(s)

    def set_summary(self, session_id:str, summary:str):
        s = self.get_or_create(session_id)
        s.summary = summary[: self.max_summary_chars]

    def set_last_risk(self, session_id:str, risk:dict):
        s = self.get_or_create(session_id)
        s.last_risk = risk

    def window(self, session_id:str) -> List[ChatMessage]:
        s = self.get_or_create(session_id)
        # return the last N messages (user+assistant)
        return s.messages[-self.max_window:]

    def get_context_blocks(self, session_id:str) -> Tuple[str, str]:
        """Return (summary_block, transcript_block) strings for prompts."""
        s = self.get_or_create(session_id)
        summary_block = f"Session summary so far: {s.summary}" if s.summary else ""
        # compact last turns
        turns = []
        for m in self.window(session_id):
            prefix = "User" if m.role == "user" else "Therapist"
            turns.append(f"{prefix}: {m.content}")
        transcript_block = "\n".join(turns)
        return summary_block, transcript_block

    def _trim(self, s: SessionState):
        # keep memory small
        if len(s.messages) > (self.max_window * 2 + 20):
            # drop older half (assistant-safe)
            s.messages = s.messages[-(self.max_window * 2):]
