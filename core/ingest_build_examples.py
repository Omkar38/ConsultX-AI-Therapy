import os, re, json, hashlib, pathlib
from datetime import date
from typing import List, Dict, Any

from time import sleep
from datasets import load_dataset
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
import chromadb

# ---------- Config ----------
OUT_JSONL   = "backend/data/vector/psych_examples.jsonl"   # optional dump for inspection
PERSIST_DIR = "backend/data/vector/psych_db"
COLLECTION  = "kb_examples"            # NEW name avoids stale locks
MODEL_NAME  = "all-MiniLM-L6-v2"
MAX_ROWS    = 10000
BATCH_SAVE_JSONL = True
INCLUDE_QUESTION = False                  # set True to embed Q + A

# Ensure path is writable
p = pathlib.Path(PERSIST_DIR)
p.mkdir(parents=True, exist_ok=True)
print("cwd:", os.getcwd(), "| persist path:", p.resolve(), "| writable:", os.access(p, os.W_OK))

# -------- SANITIZE: safer, MI-style, concise --------
_SANITIZE_RULES = [
    (re.compile(r"\byou should\b", re.I), "you might consider"),
    (re.compile(r"\byou must\b", re.I), "it may help to"),
    (re.compile(r"\byou need to\b", re.I), "it may help to"),
    (re.compile(r"\bhere's what you need to do\b", re.I), "one option could be"),
    (re.compile(r"\b(i|we)\s+diagnose\b|\bdiagnose you\b", re.I), "I can’t provide a diagnosis"),
    (re.compile(r"\b(this is|you are)\s+(bipolar|schizophrenic|borderline)\b", re.I), "I can’t provide a diagnosis"),
    (re.compile(r"\balways\b", re.I), "often"),
    (re.compile(r"\bnever\b", re.I), "rarely"),
    (re.compile(r"\s+", re.M), " "),
]
def sanitize(text: str) -> str:
    t = text.strip()
    for rx, repl in _SANITIZE_RULES:
        t = rx.sub(repl, t)
    return t.strip()

# -------- TAG RULES (regex): topics + risk signals --------
_TAG_REGEX: Dict[str, List[re.Pattern]] = {
    "anxiety":      [re.compile(r"\b(anxious|anxiety|panic|worry|worried)\b", re.I)],
    "depression":   [re.compile(r"\b(depressed|hopeless|empty|worthless|numb)\b", re.I)],
    "relationship": [re.compile(r"\b(partner|relationship|cheat(?:ing)?|trust|break[- ]?up)\b", re.I)],
    "identity":     [re.compile(r"\b(identity|who\s+i\s+am|purpose|self[- ]?worth)\b", re.I)],
    "addiction":    [re.compile(r"\b(addiction|craving|alcohol|drink(?:ing)?|drug(s)?|smok(?:e|ing))\b", re.I)],
    "sleep":        [re.compile(r"\b(sleep|insomnia|nightmare|tired|can'?t\s+sleep)\b", re.I)],
    "stress":       [re.compile(r"\b(stress(ed)?|overwhelmed|burnout)\b", re.I)],
    "work_school":  [re.compile(r"\b(work|job|boss|class|school|exam|assignment|deadline)\b", re.I)],
    "grief":        [re.compile(r"\b(grief|grieving|loss|passed away|funeral)\b", re.I)],
    "trauma":       [re.compile(r"\b(trauma|flashback|ptsd)\b", re.I)],
    "eating":       [re.compile(r"\b(eating\s+disorder|binge|purge|restrict|anorexia|bulimia)\b", re.I)],
    # risks
    "self_harm":    [re.compile(r"\b(self[- ]?harm|cutting)\b", re.I)],
    "suicidal":     [re.compile(r"\b(kill myself|suicide|suicidal|end my life|no reason to live)\b", re.I)],
    "violence":     [re.compile(r"\b(hurt (?:someone|others)|violence|attack)\b", re.I)],
    "psychosis":    [re.compile(r"\b(hear(?:ing)? voices|hallucinat\w+|seeing things|delusion)\b", re.I)],
    "substance":    [re.compile(r"\b(relapse|withdrawal|overdose)\b", re.I)],
}
_MI_OPEN    = re.compile(r"\?\s*$|^(what|how|when|where|which|could|would)\b", re.I)
_MI_AFFIRM  = re.compile(r"(it'?s understandable|it makes sense|you (?:noticed|have)|that'?s a (?:step|strength))", re.I)
_MI_REFLECT = re.compile(r"^(it sounds like|you(?:'re| are)\s+feeling|i hear)", re.I)
_MI_SUMMARY = re.compile(r"\b(in summary|to recap|what i(?:'|)m hearing)\b", re.I)

def _match_any(text: str, patterns: List[re.Pattern]) -> bool:
    return any(rx.search(text) for rx in patterns)

def infer_tags(q: str, r: str) -> List[str]:
    t = f"{q} {r}".lower()
    tags = set()
    for tag, patterns in _TAG_REGEX.items():
        if _match_any(t, patterns):
            tags.add(tag)
    rlow = r.lower().strip()
    if _MI_OPEN.search(rlow):    tags.add("open_question")
    if _MI_AFFIRM.search(rlow) or _MI_REFLECT.search(rlow): tags.add("affirmation_or_reflection")
    if _MI_SUMMARY.search(rlow): tags.add("summary_like")
    tags.add("mi_tone")
    return sorted(tags)

_ALL_META_TAGS = [
    "anxiety","depression","relationship","identity","addiction","sleep",
    "stress","work_school","grief","trauma","eating",
    "self_harm","suicidal","violence","psychosis","substance",
    "open_question","affirmation_or_reflection","summary_like","mi_tone"
]
def tags_to_flags(tags_list: List[str]) -> Dict[str, bool]:
    s = set(tags_list)
    return {f"tag_{name}": (name in s) for name in _ALL_META_TAGS}

def to_id(q: str, r: str) -> str:
    return "EXAMPLE#" + hashlib.md5((q + "||" + r).encode()).hexdigest()[:12]

def build_store(texts, metadatas, ids, persist_path: str):
    emb = SentenceTransformerEmbeddings(model_name=MODEL_NAME)
    # Prefer modern API (>=0.5.x)
    try:
        client = chromadb.PersistentClient(path=persist_path)
        # drop stale collection if present
        try:
            client.delete_collection(COLLECTION)
            sleep(0.1)
        except Exception:
            pass

        vs = Chroma(
            client=client,
            collection_name=COLLECTION,
            embedding_function=emb,
            persist_directory=persist_path,
        )

        BATCH = 256
        for i in range(0, len(texts), BATCH):
            vs.add_texts(
                texts=texts[i:i+BATCH],
                metadatas=metadatas[i:i+BATCH],
                ids=ids[i:i+BATCH],
            )
        vs.persist()
        return vs

    except AttributeError:
        # Fallback for older Chroma (<0.5) that lacks PersistentClient
        from chromadb.config import Settings
        client_settings = Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_path,
        )
        vs = Chroma(
            collection_name=COLLECTION,
            embedding_function=emb,
            persist_directory=persist_path,
            client_settings=client_settings,
        )
        BATCH = 256
        for i in range(0, len(texts), BATCH):
            vs.add_texts(
                texts=texts[i:i+BATCH],
                metadatas=metadatas[i:i+BATCH],
                ids=ids[i:i+BATCH],
            )
        vs.persist()
        return vs

def main():
    os.makedirs("kb", exist_ok=True)

    # 1) Load HF dataset
    ds = load_dataset("jkhedri/psychology-dataset", split="train")

    texts: List[str] = []
    metadatas: List[Dict[str, Any]] = []
    ids: List[str] = []

    fout = open(OUT_JSONL, "w", encoding="utf-8") if BATCH_SAVE_JSONL else None

    # 2) Build arrays
    for i, row in enumerate(ds):
        q = str(row.get("question","")).strip()
        r = str(row.get("response_j","")).strip()
        if not q or not r:
            continue

        r2   = sanitize(r)
        tags = infer_tags(q, r2)
        rid  = to_id(q, r2)

        tags_str = ",".join(tags)
        flags    = tags_to_flags(tags)

        if INCLUDE_QUESTION:
            page_text = f"Q: {q}\nA: {r2}"       # embed both Q + A
        else:
            page_text = f"Therapy-style reply example: {r2}"

        meta = {
            "id": rid,
            "type": "example",
            "tags": tags_str,                    # CSV string (Chroma wants scalars)
            "source": "jkhedri/psychology-dataset",
            # "question": q[:500],               # optional: inspect later
            **flags
        }

        texts.append(page_text)
        metadatas.append(meta)
        ids.append(rid)

        if fout:
            fout.write(json.dumps({
                "id": rid, "type": "example", "tags": tags,
                "title": "Therapy-style reply example",
                "content": r2,
                "source": {"dataset": "jkhedri/psychology-dataset"},
                "version": "v1", "lang": "en",
                "created_at": str(date.today()),
                "license": "dataset-license"
            }, ensure_ascii=False) + "\n")

        if len(ids) >= MAX_ROWS:
            break

    if fout:
        fout.close()
        print(f"Saved JSONL dump: {OUT_JSONL} ({len(ids)} rows)")

    # 3) Build Chroma vector store (safe: single client + batched add)
    persist_path = os.path.abspath(PERSIST_DIR)  # <-- avoid UnboundLocalError
    vs = build_store(texts, metadatas, ids, persist_path)
    print(f"Indexed {len(ids)} into {persist_path}/{COLLECTION} with {MODEL_NAME}")

    # 4) Quick smoke test
    qtest = "I'm anxious and struggling with trust in my relationship."
    hits = vs.similarity_search(qtest, k=3)
    print("\nSMOKE TEST — Top 3:")
    for h in hits:
        mid  = (h.metadata or {}).get("id", "<no-id>")
        tags = (h.metadata or {}).get("tags", "")
        if isinstance(tags, list): tags = ",".join(tags)
        snippet = (h.page_content or "").replace("\n"," ")
        print(f"— {mid} | tags: {tags}\n   {snippet[:140]}...\n")

if __name__ == "__main__":
    main()
