# backend/core/retrieval.py
from typing import List, Dict, Any, Optional, Tuple

try:
    # Preferred: new split package
    from langchain_community.embeddings import SentenceTransformerEmbeddings
    from langchain_community.vectorstores import Chroma
except ModuleNotFoundError:
    # Fallback: classic langchain package
    from langchain.embeddings import HuggingFaceEmbeddings as SentenceTransformerEmbeddings
    from langchain.vectorstores import Chroma



# ---- Config (matches your ingest) ----
PERSIST_DIR = "backend/data/vector/psych_db"
COLLECTION  = "kb_examples_v3"
EMB_MODEL   = "all-MiniLM-L6-v2"

# lazy singletons (Jupyter-friendly)
_emb = None
_vs  = None

def _ensure_vs() -> Chroma:
    """Load the Chroma collection built by ingest_build_examples.py"""
    global _emb, _vs
    if _emb is None:
        _emb = SentenceTransformerEmbeddings(model_name=EMB_MODEL)
    if _vs is None:
        _vs = Chroma(collection_name=COLLECTION,
                     persist_directory=PERSIST_DIR,
                     embedding_function=_emb)
    return _vs

# map your daily-functioning dimensions → kb tags (extend/tune later)
DIM_TO_TAG = {
    "Alcohol usage": "addiction",
    "Managing mood": "depression",
    "Talking to other people": "relationship",
    "Managing work/school": "work_school",
    "Following regular schedule for bedtime & sleeping enough": "sleep",
    "Coping skills to de-stress": "stress",
}

# simple risk policy for retrieval k + tag bias
# --- tune k smaller for speed while we wire things ---
# --- tune k smaller for speed while wiring ---
RISK_POLICY = {
    "Crisis": {"must_any": ["suicidal","self_harm"], "k": 5},
    "High":   {"must_any": ["suicidal","self_harm","psychosis","substance"], "k": 4},
    "Caution":{"must_any": [], "k": 3},
    "OK":     {"must_any": [], "k": 3},
}

def _build_filter(risk_tier: str, dims: Optional[List[str]]) -> Optional[Dict[str, Any]]:
    """
    0 conds  -> None
    1 cond   -> single condition dict (no $or)
    2+ conds -> {"$or": [ ... ]}
    """
    policy = RISK_POLICY.get(risk_tier, RISK_POLICY["OK"])
    conds: List[Dict[str, Any]] = [{f"tag_{t}": True} for t in policy["must_any"]]

    if dims:
        for d in dims:
            t = DIM_TO_TAG.get(d)
            if t:
                conds.append({f"tag_{t}": True})

    if not conds:
        return None
    if len(conds) == 1:
        return conds[0]
    return {"$or": conds}

def _coerce_where(where: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """If someone passed {'$or': [single]} fix it to single; leave others as-is."""
    if not where:
        return None
    if isinstance(where, dict) and "$or" in where:
        exprs = where["$or"]
        if isinstance(exprs, list) and len(exprs) == 1:
            return exprs[0]  # <- fix single-item $or
    return where

def retrieve_context(
    user_text: str,
    risk: Dict[str, Any],
    k_override: Optional[int] = None
) -> Tuple[str, List[Any]]:
    vs = _ensure_vs()
    tier = risk.get("tier", "OK")
    dims = risk.get("dimensions") or []
    policy = RISK_POLICY.get(tier, RISK_POLICY["OK"])
    k = k_override or policy["k"]

    where = _coerce_where(_build_filter(tier, dims))

    # primary: filtered search with safe fallbacks
    try:
        if where:
            docs = vs.similarity_search(user_text, k=k, filter=where)
        else:
            docs = vs.similarity_search(user_text, k=k)
    except ValueError:
        # If Chroma still objects, retry without filter
        docs = vs.similarity_search(user_text, k=k)

    # backfill if filtered pool is too small
    if len(docs) < k:
        try:
            extra = vs.similarity_search(user_text, k=k)
            seen = set(id(d) for d in docs)
            docs += [d for d in extra if id(d) not in seen][: max(0, k - len(docs))]
        except Exception:
            pass

    lines = []
    for d in docs:
        snippet = (d.page_content or "").replace("\n", " ")[:700]
        lines.append(f"- {snippet}")
    return "\n".join(lines), docs
