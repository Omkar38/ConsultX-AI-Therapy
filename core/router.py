# backend/core/router.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer, util


# Minimal, fast hybrid: dense + sparse, per route with examples.
@dataclass
class Route:
    name: str
    kind: str  # "allow" | "deny" | "crisis"
    examples: List[str]
    dense_centroid: Optional[np.ndarray] = None
    sparse_vec: Optional[np.ndarray] = None

class HybridRouter:
    def __init__(self,
                 dense_model: str = "all-MiniLM-L6-v2",
                 deny_threshold: float = 0.62,
                 allow_threshold: float = 0.55,
                 crisis_kw: List[str] = None):
        self.embed = SentenceTransformer(dense_model)
        self.routes: List[Route] = []
        self.vectorizer = None  # fitted later
        self.deny_threshold = deny_threshold
        self.allow_threshold = allow_threshold
        self.crisis_kw = crisis_kw or [
            "kill myself","suicide","end my life","want to die","take my own life"
        ]

    def add_route(self, name: str, kind: str, examples: List[str]):
        self.routes.append(Route(name=name, kind=kind, examples=examples))

    def fit(self):
        # dense centroids
        for r in self.routes:
            emb = self.embed.encode(r.examples, convert_to_tensor=True, normalize_embeddings=True)
            r.dense_centroid = emb.mean(dim=0)
        # sparse vectors
        all_text = []
        for r in self.routes:
            all_text.append(" \n ".join(r.examples))
        self.vectorizer = TfidfVectorizer(ngram_range=(1,2), min_df=1)
        mats = self.vectorizer.fit_transform(all_text)
        for i, r in enumerate(self.routes):
            r.sparse_vec = mats[i]

    def _dense_score(self, text: str, r: Route) -> float:
        q = self.embed.encode([text], convert_to_tensor=True, normalize_embeddings=True)
        return float(util.cos_sim(q, r.dense_centroid)[0][0])

    def _sparse_score(self, text: str, r: Route) -> float:
        if not self.vectorizer:
            return 0.0
        q = self.vectorizer.transform([text])
        # cosine on sparse
        num = q.multiply(r.sparse_vec).sum()
        denom = (np.linalg.norm(q.toarray()) * np.linalg.norm(r.sparse_vec.toarray()) + 1e-9)
        return float(num / denom)

    def _kw_crisis(self, text: str) -> bool:
        t = text.lower()
        return any(k in t for k in self.crisis_kw)

    def route(self, text: str) -> Tuple[str, float]:
        if self._kw_crisis(text):
            return ("crisis", 1.0)
        best = ("none", 0.0)
        for r in self.routes:
            d = self._dense_score(text, r)
            s = self._sparse_score(text, r)
            hybrid = 0.6 * d + 0.4 * s
            if hybrid > best[1]:
                best = (f"{r.kind}:{r.name}", hybrid)
        # thresholding logic: prefer deny > allow if both above thresh
        label, score = best
        if label.startswith("deny") and score >= self.deny_threshold:
            return (label, score)
        if label.startswith("allow") and score >= self.allow_threshold:
            return (label, score)
        return ("none", score)

def default_router() -> HybridRouter:
    r = HybridRouter()
    # deny (out of scope): diagnosis, meds, illegal advice, hate/harassment
    r.add_route("clinical_diagnosis", "deny", [
        "Do I have bipolar?", "Can you diagnose me?", "What medication should I take?",
        "Prescribe me antidepressants", "What dose of Xanax should I take?"
    ])
    r.add_route("illegal_or_harm", "deny", [
        "How do I hurt someone?", "How can I hide a crime?", "How to get illegal drugs",
        "How do I self-harm safely?"
    ])
    # allow (in scope): MI/CBT supportive topics
    r.add_route("support_relationship", "allow", [
        "My partner cheated", "I feel betrayed", "I can’t trust anyone",
        "We keep fighting and I feel broken"
    ])
    r.add_route("support_school_work", "allow", [
        "I’m overwhelmed with school", "My job is stressing me out",
        "I’m failing my exams", "I can’t focus at work"
    ])
    r.add_route("support_lonely_identity", "allow", [
        "I feel lonely", "I’m homesick", "I’m struggling with identity",
        "I feel lost about who I am"
    ])
    r.add_route("support_addiction", "allow", [
        "I’ve been drinking most nights", "I’m worried about relapse",
        "I’m struggling with addiction", "I use alcohol to cope"
    ])
    r.fit()
    return r
