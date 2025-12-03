# ConsultX Backend

This backend powers the **ConsultX** AI therapy companion.  
It wraps a full safety-aware pipeline:

- **Risk engine** (emotion + lexical + dimensions) → `OK / Caution / High / Crisis`
- **Retrieval** over CBT/MI content using ChromaDB
- **LLM orchestration** (Gemini) with conversation memory
- **Guardrails** for Motivational Interviewing (MI) style and crisis handling
- A single public API your frontend / teammates can call.

---

## 1. Project Structure

```text
backend/
  api/
    main.py                # FastAPI app exposing /api/v1/chat
  core/
    __init__.py
    orchestrator.py        # main pipeline entry: run_generate_reply(...)
    prompt.py              # builds MI/CBT LLM prompt
    retrieval.py           # ChromaDB + sentence transformers
    router.py              # (optional) classic routing / fallback
    risk_types.py          # risk engine: emotions, self-harm lexicon, dimensions
    guardrails.py          # MI style + safety templates + hotline responses
    llm_gateway.py         # Gemini client wrapper
    memory.py              # conversation memory helpers
    session_store.py       # in-memory / per-session transcript store
    schemas.py             # Pydantic models for API (ChatRequest, ChatResponse, etc.)
  eval/
    harness.py             # evaluation harness for pipeline
    test_cases.jsonl       # risk / guardrail test definitions (optional)
  ingest/
    ingest_build_examples.py  # builds ChromaDB from CBT/MI content
  requirements.txt
  README_BACKEND.md        # this file
```

> **Public API surface**: teams should only depend on  
> - `POST /api/v1/chat` (HTTP)  
> - or Python call to `orchestrator.run_generate_reply(...)`  
> Everything else is internal.

---

## 2. Environment & Installation

### Python version

Recommended:

- **Python 3.10 or 3.11**
- Avoid base Anaconda env; use a clean venv.

From the repo root:

```bash
cd backend

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt
```

> If you ever see SciPy / NumPy errors, make sure you are **inside this venv** and not using the global conda environment.

### Required environment variables

Set these before running anything:

```bash
# Gemini API key
export GEMINI_API_KEY="your_key_here"

# Where to store / read the vector DB
export CHROMA_DB_DIR="./chroma_db"

# Optional: for logging / toggles
export CONSULTX_ENV="dev"
```

---

## 3. Building the Knowledge Base (ChromaDB)

Before serving requests, you need to build the vector store used by `retrieval.py`.

From `backend/`:

```bash
source .venv/bin/activate

# Make sure CHROMA_DB_DIR is set
export CHROMA_DB_DIR="./chroma_db"

# Run ingestion
python -m backend.ingest.ingest_build_examples
```

This will:

- Load CBT/MI reference snippets
- Embed them with sentence transformers
- Store them into a persistent Chroma collection under `CHROMA_DB_DIR`.

---

## 4. Running the FastAPI Server

The backend exposes a simple HTTP API via FastAPI.

**File:** `backend/api/main.py` (simplified view)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core import orchestrator as orch
from backend.core.schemas import ChatRequest, ChatResponse

app = FastAPI(title="ConsultX Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    out = orch.run_generate_reply(
        user_text=req.message,
        k=req.k or 4,
        model=req.model or "gemini-2.0-flash",
        country_code=req.country_code or "US",
        session_id=req.session_id,
    )
    return ChatResponse(
        reply=out["reply"],
        risk=out["risk"],
        guardrail_action=out.get("guardrail_action"),
        guardrail_notes=out.get("guardrail_notes", []),
        session_id=out.get("session_id", req.session_id),
    )

@app.get("/api/v1/health")
async def health():
    return {"status": "ok"}
```

Run it:

```bash
cd backend
source .venv/bin/activate

uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Now your backend is available at:

- `http://localhost:8000/api/v1/health`
- `http://localhost:8000/api/v1/chat`

---

## 5. API Contract

### `POST /api/v1/chat`

**Request body (`ChatRequest`):**

```json
{
  "message": "I feel homesick and my friends are ghosting me.",
  "session_id": "optional-stable-id-per-conversation",
  "model": "gemini-2.0-flash",
  "country_code": "US",
  "k": 4
}
```

Fields:

- `message` *(string, required)* – user utterance.
- `session_id` *(string, optional)* – stable ID to keep conversation memory. If omitted, backend can create one.
- `model` *(string, optional)* – LLM name; defaults to `"gemini-2.0-flash"`.
- `country_code` *(string, optional)* – used for safety text (e.g., hotline patterns); default `"US"`.
- `k` *(int, optional)* – number of RAG snippets to retrieve.

**Response body (`ChatResponse`):**

```json
{
  "reply": "Therapist-style text...",
  "risk": {
    "tier": "Caution",
    "score": 1.0,
    "emotion": "sadness",
    "dimension": "Expressing feelings to other people",
    "dimensions": [
      "Expressing feelings to other people",
      "Managing work/school",
      "Participation in community"
    ],
    "confidence": 0.5,
    "notes": [
      "emotion=sadness:0.99",
      "zsl_dims_used",
      "top_dimension=Expressing feelings to other people",
      "negative_emotion"
    ]
  },
  "guardrail_action": "soften",
  "guardrail_notes": [
    "Full MI pass applied."
  ],
  "session_id": "same-id-to-reuse-next-turn"
}
```

**Interpretation:**

- `reply` – the MI-style therapist response the UI shows.
- `risk` – structured metadata from `risk_types.assess`:
  - `tier`: `OK | Caution | High | Crisis`
  - `score`: 0–3 risk score
  - `emotion`: top emotion from the emotion classifier
  - `dimension(s)`: CBT/MI “life area” hints (work, relationships, safety, etc.)
- `guardrail_action`:
  - `"ok"` – LLM reply passed with minimal edits.
  - `"soften"` – MI / safety guardrails applied (extra reflection, safety line).
  - `"crisis_override"` – direct crisis template (911 + 988) used.
- `guardrail_notes` – debug/internal notes (e.g., `Crisis override (risk tier or suicide keywords in user text).`).
- `session_id` – pass this back in the next request to preserve memory.

**Example cURL:**

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I just moved for my masters and my friends are ghosting me. I feel really homesick.",
    "session_id": "demo-session-1"
  }'
```

---

## 6. Internal Architecture

High-level flow inside `orchestrator.run_generate_reply`:

```text
User message
   |
   v
[Risk Engine]  (risk_types.py)
 - Emotion model (sadness, fear, anger, disgust, etc.)
 - Self-harm & mitigation lexicons
 - Dimension classifier (e.g., "Suicidal ideation", "Managing work/school")
   |
   +--> Crisis override? (explicit self-harm language or very high score)
   |        |
   |        +--> [Crisis Template] (guardrails.py)
   |              - 911 / 988 guidance
   |              - No MI exploration, pure safety
   |        |
   |        '--> return crisis reply + risk
   |
   '--> Non-crisis → continue
           |
           v
    [Retrieval]  (retrieval.py)
      - ChromaDB + SentenceTransformer
      - Top-k CBT/MI guidance snippets
           |
           v
    [Prompt Builder] (prompt.py)
      - System: non-clinical, MI + brief CBT structure
      - Style checklist (OARS, 5–9 sentences, 1 open question, 1 tiny step)
      - Include: risk hints (tier, emotion, dimensions)
      - Include: retrieved snippets + short history summary
           |
           v
    [LLM Gateway] (llm_gateway.py → Gemini)
           |
           v
    [Guardrails] (guardrails.py)
      - Normalize “Therapist:” prefix
      - Ensure MI checklist (reflection, affirmation, open question)
      - Enforce safety: hotline text for Crisis, no advice-y “must/should”
           |
           v
    [Memory] (memory.py, session_store.py)
      - Update history summary & transcript for session_id
           |
           v
    Final response:
      - therapist reply (string)
      - risk object (dict)
      - guardrail_action / guardrail_notes
      - session_id
```

---

## 7. Evaluation Harness

The evaluation harness runs a suite of test cases through the full pipeline and logs metrics.

**File:** `backend/eval/harness.py`

Typical usage:

```bash
cd backend
source .venv/bin/activate

export GEMINI_API_KEY="..."
export CHROMA_DB_DIR="./chroma_db"

python -m backend.eval.harness
```

This will:

- Load ~40 test cases (OK / Caution / High / Crisis, various scenarios)
- Call `orchestrator.run_generate_reply` for each
- Write a JSONL file like:

```text
backend/eval/results/eval_results_YYYYMMDD_HHMMSS.jsonl
```

Each line includes:

- `case_id`, `expected_tier`
- `detected_tier`, `risk`, `guardrail_action`
- Flags for MI correctness (reflection, open question)  
- Whether hotline text was used when expected

It also prints summary stats, e.g.:

- Risk tier accuracy
- Guardrail action match rate
- Hotline correctness
- Confusion matrix (expected vs detected tiers)

You can reference this in your report / presentation as your **internal QA for safety + behavior**.

---

## 8. Frontend Integration

From the frontend (e.g., `frontend/ConsultX`):

Configure base URL in your environment:

```bash
VITE_CONSULTX_API_BASE=http://localhost:8000
```

Simple client example (TypeScript / React):

```ts
async function sendMessage(message: string, sessionId?: string) {
  const res = await fetch(
    `${import.meta.env.VITE_CONSULTX_API_BASE}/api/v1/chat`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId }),
    }
  );
  if (!res.ok) throw new Error("ConsultX API error");
  return res.json();
}
```

In your chat component:

```ts
const [sessionId, setSessionId] = useState<string | undefined>();

async function handleSend(text: string) {
  const resp = await sendMessage(text, sessionId);
  setSessionId(resp.session_id);
  // Add resp.reply to chat messages
  // Optionally show resp.risk.tier as a badge
}
```

That’s all the frontend needs to know — the rest of the complexity stays encapsulated inside `backend/core`.

---

## 9. Summary

- `backend/core/*` holds your **AI therapy engine** (risk + RAG + LLM + guardrails + memory).
- `backend/api/main.py` exposes a **simple HTTP API** for other teams.
- `backend/eval/harness.py` gives you a **repeatable evaluation matrix** (tiers, guardrails, hotline).
- `CHROMA_DB_DIR` + ingestion script let you swap/update the knowledge base without changing code.

This README is meant for **backend + infra + frontend teammates** so they can plug in the pipeline, understand the safety behavior, and debug issues without diving into every file.
