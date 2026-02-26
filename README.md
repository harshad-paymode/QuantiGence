## Table of Contents

- [Vision & Summary](#vision--summary)  
- [Highlights & Strengths](#highlights--strengths)  
- [Project Scope (Why it’s “grand”)](#project-scope-why-its-grand)  
- [High-level Architecture](#high-level-architecture)  
- [Knowledge Graph — design & schema](#knowledge-graph---design--schema)  
  - [Core Nodes](#core-nodes)  
  - [Core Relationships](#core-relationships)  
- [Core Pipeline (Supervisor → Auditor → Researcher → Analyst)](#core-pipeline-supervisor----auditor----researcher----analyst)  
  - [Supervisor](#supervisor)  
  - [Researcher](#researcher)  
  - [Auditor](#auditor)  
  - [Analyst](#analyst)  
- [Context reuse & multi-turn memory](#context-reuse--multi-turn-memory)  
- [Persistence & DB choices (Cosmos DB, Redis, Neo4j, parquet)](#persistence--db-choices-cosmos-db-redis-neo4j-parquet)  
- [Prompts & Grounding policy (examples)](#prompts--grounding-policy-examples)  
- [Safety & Evaluation (Auditor + DeepEval)](#safety--evaluation-auditor--deepeval)  
- [Quickstart (dev)](#quickstart-dev)  
- [Future work / Roadmap](#future-work--roadmap)  
- [Contributing & testing](#contributing--testing)  
- [License](#license)  
- [Disclaimer](#disclaimer)


# QuantiGence

> Hybrid Financial Intelligence Platform  
> Quantitative analytics × Knowledge Graph × LLM-powered qualitative reasoning × Evaluation-first design

## Demo

*Demo: end-to-end query → retrieval → audit → final narrative with DeepEval scores and synchronized OHLC candlestick chart.*

https://github.com/user-attachments/assets/1d0f6cd1-684b-4f2f-ac83-ee51424f25d8

*Ratios table view alongside management commentary — category filters, period selection, and provenance-backed narrative.*

<img width="1892" height="865" alt="preview1" src="https://github.com/user-attachments/assets/a3cd547d-43ca-4f8b-97bb-371eb354a27a" />

*Split-screen overview showing Qualitative AI (left) and Quantitative dashboard (right) — synchronized context, query input, and the risk chart.*

<img width="1887" height="877" alt="preview3" src="https://github.com/user-attachments/assets/b212a53b-a26d-4dfa-ab9b-87e4e98ae992" />



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
- **Data Sources**  
  Raw inputs: market data (Parquet) and Earnings call transcripts (downloaded through AlphaVantage and financetoolkit), full-text 10-K and 10-Q SEC filings (downloaded using egartools pypi package).
- **Storage Layer**  
  A polyglot persistence approach:
  - *Parquet* for compact, fast time-series reads and analytics.
  - *Neo4j* (or similar graph DB) to store entities, roles, and cross-document links for multi-hop queries.
  - *Redis* for low-latency orchestration state, caching, and session memory.
  - *Cosmos DB / document store* for durable metadata, user preferences, and exported provenance.

- **Orchestration Layer**  
  The Supervisor orchestrates work and enforces policies. Distinct role-workers carry out:
  - *Researcher* — retrieves passages, KG facts, and numeric slices.
  - *Auditor* — verifies LLM outputs against sources and assigns evaluation scores.
  - *Analyst* — composes the final, citation-backed narrative delivered to users.

- **API Layer**  
  A lightweight HTTP layer (FastAPI) exposes endpoints to the UI and enqueues long-running tasks. Task workers perform background pipelines and results are polled or pushed back to the frontend.

- **Frontend**  
  Presents synchronized quantitative visuals and qualitative narratives, shows provenance links, and displays evaluation scores (DeepEval). Designed for interactive, multi-turn analyst workflows.

### Design goals reflected in the architecture

- **Separation of concerns** — data, reasoning, verification, and presentation are modular.  
- **Provenance & auditability** — every generated claim is traceable to data slices or node relationships.  
- **Scalability** — parquet + async tasks + caching enable efficient handling of large time-series and heavy retrieval.  
- **Safety-first orchestration** — an explicit Auditor role and evaluation metrics reduce hallucination risk and support human-in-the-loop review.

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
1. Clone the Repository Using
```bash
https://github.com/harshad-paymode/QuantiGence.git
```
2. Install Poetry from PyPi
```bash
pip install poetry==2.2.1
```
3. Install Poetry from PyPi
```bash
pip install poetry==2.2.1
```

4. To install the defined dependencies for QuantiGence, just run

```bash
poetry install
```

5. Configure environment variables in a given .env file
6. Start backend API and task worker

```bash
#Run The Backend servers with Docker Redis task worker and FastApi
docker-compose up --build
#OR
#Run the below commands in separate terminals
fastapi dev main.py
celery -A tasks worker --loglevel=info
```

7. Start frontend

```bash
#Start frontend in a separate terminal
npm run dev
```
   
8. Submit qualitative query
9. View charts + AI response + evaluation scores

The above setup is given for Windows Operating system using Command Prompt.

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

## License

QuantiGence is licensed under the Apache License 2.0. See the LICENSE file for full terms and conditions.

## Disclaimer

QuantiGence is a financial research and analytics tool intended to provide informational insights based on publicly available data, including SEC filings and historical market data. Any forecasts, projections, or analyses generated by the system are based on statistical patterns and should not be interpreted as financial, investment, or trading advice. Users should conduct their own due diligence or consult a qualified financial professional before making any investment decisions.
