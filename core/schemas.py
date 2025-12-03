from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from dataclasses import dataclass, field
import time

class RiskSignal(BaseModel):
    tier: str = Field(default="OK", description="OK | Caution | High | Crisis")
    score: int = 0
    emotion: Optional[str] = None
    dimensions: Optional[List[str]] = None  # your daily-functioning dims
    confidence: Optional[float] = None

class RetrievedDoc(BaseModel):
    id: str
    content: str
    tags: str
    score: Optional[float] = None
    meta: Dict[str, Any] = {}

class RetrievalParams(BaseModel):
    k: int = 5
    use_filters: bool = True
    mmr: bool = False  # can enable later

class RAGRequest(BaseModel):
    user_text: str
    risk: RiskSignal
    retrieval: Optional[RetrievalParams] = None

class RAGResponse(BaseModel):
    reply: str
    used_docs: List[RetrievedDoc]
    prompt_echo: Optional[str] = None
    notes: Optional[Dict[str, Any]] = None

@dataclass
class ChatMessage:
    role: str           # "user" | "assistant" | "system"
    content: str
    ts: float = field(default_factory=lambda: time.time())

@dataclass
class SessionState:
    session_id: str
    messages: List[ChatMessage] = field(default_factory=list)
    summary: str = ""           # rolling summary (short)
    last_risk: Optional[Dict[str, Any]] = None

# Optional: light log unit
@dataclass
class TurnLog:
    session_id: str
    user_text: str
    reply_text: str
    risk: Dict[str, Any]
    guardrail_action: str
    guardrail_notes: str
    ts: float = field(default_factory=lambda: time.time())

