# ConsultX — Retrieval-Augmented Guardrails for Safer AI Therapy

ConsultX prevents over-affirmation and unsafe responses by grounding the LLM in vetted CBT/MI content (RAG) and enforcing post-generation safety checks. No fine-tuning required — everything runs through prompts, retrieval, and guardrails.

---

## 1. Overview

This branch contains the **full ConsultX stack**:

- A **Python backend** for:
  - Conversation **session tracking** (with rolling buffers).
  - **Risk scoring** across tiers: `ok`, `caution`, `high`, `crisis`.
  - **End-of-session summaries** for analysis & research.
  - An optional **therapy RAG pipeline** (Gemini + curated CBT/MI snippets + guardrails).

- A **React + TypeScript + Vite frontend** for:
  - Chat-style UI on top of the backend API.
  - Live view of messages, risk tiers, and session context.

This repo is meant to be **research-friendly**: easy to run locally, inspect, and extend for analysis & safety experiments.

---

## 2. Key Features

- 🧠 **MI + CBT-style responses**: Prompting and retrieval are tuned toward psycho-educational, non-diagnostic, MI/CBT-flavored guidance.
- 🛟 **Guardrail-first design**:
  - Pre-message safety checks and risk tiers.
  - Retrieval from vetted resources only.
  - Post-generation filters to catch over-affirmation, unsafe suggestions, and policy violations.
- 📊 **Session tracking & summaries**:
  - Rolling buffer of recent turns.
  - Per-session risk metrics & sentiment trends.
  - Structured JSON summary ready for downstream analysis.
- 🧩 **Modular core**:
  - `backend/core/*` isolates RAG, LLM calls, guardrails, and risk types.
  - `backend/session_tracking.py` handles session lifecycle & metrics.
  - Easy to swap in different LLMs or retrieval backends.
- 🌐 **Simple HTTP API**:
  - Built on the Python standard library.
  - Stateless endpoints plus SQLite persistence layer.
- 💻 **Modern frontend**:
  - React + TypeScript + Vite dev server.
  - Ready to wire to any backend endpoint.

---

## 3. Architecture at a Glance

High-level pipeline for a **therapy turn**:

```text
User message
   │
   ▼
[Step 1] Safety Gate (risk + policy check)
   - Keyword-based risk detection (ok / caution / high / crisis)
   - Lightweight sentiment & intent heuristics
   │
   ▼
[Step 2] Curated Knowledge Retrieval
   - Retrieve CBT/MI snippets from vetted psycho-educational sources
   - Top-k context chunks for this turn
   │
   ▼
[Step 3] Contextual Response Generation
   - LLM (e.g., Gemini) + MI/CBT prompt template
   - Uses retrieved context + risk tier rules
   │
   ▼
[Step 4] Guardrail Enforcement Layer
   - Post-generation filters for unsafe / over-affirmative patterns
   - Crisis escalation messaging, disclaimers, and safe deflections
   │
   ▼
Persisted in SQLite + exposed to the frontend for analysis & UX

The session tracker runs alongside this pipeline, storing:
  - All messages + timestamps.
  - Risk scores and tier transitions.
  - Final session summary with trends & resource hints.

text```

The session tracker runs alongside this pipeline, storing:
All messages + timestamps.
Risk scores and tier transitions.
Final session summary with trends & resource hints.

##4. Project Structure

TheConsultX/
├── backend/
│   ├── __init__.py
│   ├── analysis.py            # Sentiment + risk heuristics & resource mapping
│   ├── api.py                 # HTTP server exposing REST endpoints
│   ├── models.py              # Dataclasses, enums, and shared types
│   ├── session_tracking.py    # Session lifecycle + metrics + summaries
│   ├── storage.py             # SQLite repository for sessions/messages/metrics
│   ├── core_adapter.py        # Thin wrapper: session tracker → RAG/guardrails core
│   └── core/                  # RAG + LLM + guardrails pipeline
│       ├── orchestrator.py    # Orchestrates retrieval → LLM → guardrails
│       ├── retrieval.py       # Vector store + embeddings + top-k snippet lookup
│       ├── prompt.py          # MI/CBT system & turn templates
│       ├── guardrails.py      # Post-gen filters, safety rules, escalation logic
│       ├── risk_types.py      # Canonical risk tiers and helper types
│       ├── llm_gateway.py     # Wrapper over Gemini / LLM API(s)
│       ├── memory.py          # Long-lived memory abstraction (per user/episode)
│       ├── session_store.py   # Persistent store for core pipeline state
│       ├── schemas.py         # Pydantic-style schemas for RAG/therapy turn payloads
│       └── ingest_build_examples.py
│                              # Scripts to ingest CBT/MI resources into a vector store
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── eslint.config.js
│   ├── prettier.config.js
│   └── src/
│       ├── main.tsx           # React entrypoint
│       ├── App.tsx            # Top-level app shell
│       ├── components/        # Chat UI, risk badges, layout components, etc.
│       └── ...
│
├── docs/
│   └── session_backend_design.md   # Detailed design doc for session tracking backend
│
├── consultx.db                # SQLite database (created/used by backend)
├── responses.json             # Example RAG / guardrail responses for reference
└── README.md                  # You are here
