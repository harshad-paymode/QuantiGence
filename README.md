# QuantiGence

> Hybrid Financial Intelligence Platform  
> Quantitative analytics × Knowledge Graph × LLM-powered qualitative reasoning × Evaluation-first design

## Vision & Summary

QuantiGence is a financial research and analytics platform designed to unify structured financial analysis with LLM-driven qualitative reasoning.

It combines:
- Historical market data
- SEC filings and corporate disclosures
- A Knowledge Graph of entities and relationships
- A supervised, auditable LLM orchestration pipeline

The goal is to produce grounded, citation-backed, evaluation-scored financial insights — not just answers.

QuantiGence is built for researchers, analysts, and engineers who want transparent, reproducible AI-assisted financial intelligence.

## Highlights & Strengths

- **Hybrid Intelligence Architecture** — deterministic financial analytics + probabilistic LLM reasoning
- **Knowledge Graph Backbone** — entity-centric modeling for relationship discovery
- **Audited LLM Responses** — faithfulness and relevancy scoring
- **Provenance-first Design** — traceable evidence from filings and data
- **Multi-turn Context Memory** — supports analytical workflows
- **Evaluation-Driven Outputs** — built-in DeepEval scoring
- **Task-Oriented Orchestration** — Supervisor-driven role separation
- **Scalable Data Model** — parquet-based analytics + graph-based reasoning

## High-level Architecture
Data Sources
│
├── Market Time Series (Parquet)
├── SEC Filings
└── Earning's Call Transcript
│
▼
Storage Layer
│
├── Parquet (analytics)
├── Neo4j (knowledge graph)
├── Redis (task state & memory)
└── Cosmos DB (persistent metadata)
│
▼
Orchestration Layer
│
Supervisor
├── Researcher
├── Auditor
└── Analyst
│
▼
API Layer
│
FastAPI + Task Workers
│
▼
Frontend
│
Quantitative Dashboard + Qualitative AI

## Knowledge Graph — design & schema

QuantiGence models financial intelligence as an entity network.

### Core Nodes

- **Company**
- **Filing**
- **Section**
- **Metric**
- **Event**
- **Person**

### Core Relationships

- Company → HAS_FILING → Filing
- Filing → CONTAINS → Section
- Company → REPORTED_METRIC → Metric
- Company → EXPERIENCED → Event
- Person → HELD_ROLE_AT → Company

### Why It Matters

- Enables multi-hop reasoning
- Connects textual disclosures to numeric trends
- Supports temporal and relational analysis
- Provides grounding context for LLM responses

The Knowledge Graph transforms documents into structured intelligence.

## Core Pipeline (Supervisor → Auditor → Researcher → Analyst)

QuantiGence uses a structured multi-role orchestration model.

### Supervisor
- Routes tasks
- Manages memory
- Enforces grounding policy
- Controls workflow lifecycle

### Researcher
- Retrieves relevant filings and data
- Extracts structured evidence
- Produces candidate summaries

### Auditor
- Evaluates responses for faithfulness
- Checks for hallucinations
- Scores relevancy
- Flags unsupported claims

### Analyst
- Synthesizes final response
- Integrates evidence
- Formats citations
- Produces user-ready narrative

This separation improves reliability and reduces hallucination risk.

## Context reuse & multi-turn memory

QuantiGence supports structured analytical workflows.

### Short-term Memory
- Session-based conversation context
- Recent queries and outputs

### Long-term Memory
- Persisted preferences
- Prior validated findings
- Watchlists and tracked entities

### Intelligent Context Selection
- Recency-based prioritization
- Relevance-based filtering
- Controlled context window growth

This enables consistent multi-turn research sessions without context drift.

## Persistence & DB choices (Cosmos DB, Redis, Neo4j, parquet)

QuantiGence uses polyglot persistence.

### Parquet
- Efficient columnar storage
- Optimized for financial time-series analytics
- High compression and fast reads

### Redis
- Task queue backend
- Orchestration state
- Short-term session memory
- Caching layer

### Neo4j
- Knowledge Graph storage
- Multi-hop entity traversal
- Relationship-based reasoning

### Cosmos DB
- Flexible metadata storage
- Persistent application state
- Distributed document storage

Each system is chosen for what it does best.

## Prompts & Grounding policy (examples)

QuantiGence enforces grounding-first LLM design.

### Grounding Rules

- Every factual claim must be supported by evidence
- Numeric claims must reference source tables
- Uncertainty must be acknowledged
- If unsupported → the model must abstain

### Prompt Design Philosophy

- Retrieval-aware prompts
- Citation-required generation
- Structured verification loops
- Role-specific instructions (Researcher vs Auditor vs Analyst)

This reduces hallucinations and increases interpretability.

## Safety & Evaluation (Auditor + DeepEval)

Evaluation is built into the pipeline.

### Auditor Role
- Verifies claims against retrieved evidence
- Detects unsupported assertions
- Flags contradictions

### DeepEval Metrics
- **Faithfulness** — Is the answer supported?
- **Relevancy** — Is it answering the actual question?
- **Coverage** — Was important information omitted?

Each response includes evaluation scoring for transparency.

## Quickstart (dev)

### Requirements

- Python 3.11+
- Poetry
- Node.js (for frontend)
- Redis
- Access to parquet data
- Optional: Neo4j instance

### High-Level Steps

1. Install dependencies
2. Configure environment variables
3. Start backend API
4. Start task worker
5. Start frontend
6. Submit qualitative query
7. View charts + AI response + evaluation scores

If local resources are constrained, run backend services remotely and connect frontend via API base URL.

## Future work / Roadmap

Planned expansions:

- Expand Knowledge Graph node types and relationships
- Introduce temporal relationship modeling
- Detect recurring financial patterns using graph motifs
- Add anomaly detection on reporting trends
- Incorporate human-in-the-loop correction loops
- Improve audit trace exportability
- Enable enterprise deployment modes

The next major milestone is deepening the Knowledge Graph to support pattern discovery, cross-company inference, and structural event modeling.

---

## Contributing & testing

Contributions are welcome.

- Fork the repository
- Create feature branch
- Submit pull request
- Include tests and documentation

Testing philosophy:
- Unit tests for data processing
- Integration tests for retrieval
- End-to-end evaluation tests for LLM pipeline
- Reproducible evaluation metrics

---

## License

MIT License.

---

## Disclaimer

QuantiGence is a financial research and analytics tool intended to provide informational insights based on publicly available data, including SEC filings and historical market data. Any forecasts, projections, or analyses generated by the system are based on statistical patterns and should not be interpreted as financial, investment, or trading advice. Users should conduct their own due diligence or consult a qualified financial professional before making any investment decisions.

---
