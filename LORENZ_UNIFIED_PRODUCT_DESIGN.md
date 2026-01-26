LORENZ Unified Product Design (Core + Gateway)
==============================================

Scope
-----
This document defines the unified LORENZ product that blends the best parts of the
current LORENZ stack and the Clawdbot codebase. Clawdbot must be invisible to the
outside world. Internally it is treated as a gateway/runtime and tool standard.

Goals
-----
- LORENZ is the only visible brand, CLI, UI, docs, and config surface.
- Multi-tenant SaaS core with strong isolation and EU data residency.
- All Clawdbot skills available in MVP via a single skill registry.
- Hybrid RAG with vector + BM25 + RRF + reranking as a first-class feature.
- Real-time digital twin: voice cloning + 3D avatar interaction (opt-in).
- RSI loop for continuous quality improvements with strict guardrails.

Non-goals
---------
- No public exposure of Clawdbot naming or artifacts.
- No hard rewrite of every skill on day one; adapters allowed.

Requirements (Confirmed)
------------------------
- Skills: all Clawdbot skills included in MVP registry.
- Channels: Telegram + WhatsApp first, then Teams + Slack.
- Data residency: EU only.

High-level Architecture
-----------------------

Channels -> LORENZ Gateway -> LORENZ Core -> RAG/Skills/RSI/Storage

1) LORENZ Gateway (Edge)
   - Ingests messages from channels.
   - Executes device-local skills (apple notes, imessage, voice, etc).
   - Maintains session state and tool execution.
   - Communicates with LORENZ Core via secure API.

2) LORENZ Core (SaaS, EU)
   - Tenant isolation, auth, billing, analytics.
   - RAG pipeline (ingest, hybrid search, reranking).
   - Skill registry, permissions, and execution routing.
   - RSI pipeline for tuning ranking and tool routing.

Branding
--------
- External surfaces must show LORENZ only.
- No "clawdbot" in CLI commands, config keys, UI labels, or docs.
- Internal code may keep legacy names, but must be encapsulated.

Skill System (Unified Standard)
-------------------------------
Standard: Clawdbot tool schema and lifecycle.

Execution targets:
- core_only: stateless or data-centric skills.
- edge_only: device-local skills (iMessage, Apple Notes, Things, tmux).
- hybrid: tools that run locally but call core for RAG or data.

Implementation strategy:
- Keep all Clawdbot skills as-is in the gateway runtime.
- Central skill registry in Core controls enablement per tenant,
  and exposes policy flags: enabled, edge_only, requires_api, requires_device.

Skill Flow (God vs Emergent)
----------------------------
God Skills:
- Preinstalled or added over time by the core team.
- Versioned, reviewed, and shipped with the LORENZ registry.
- Can be enabled per tenant with policy gating.

Emergent Skills:
- Learned from successful workflows or repeated user actions.
- Stored as skill blueprints with triggers, inputs, and actions.
- Require review/approval before promotion or tenant-wide enablement.

Flow:
1) User request -> Router selects candidate skill(s).
2) Skill executes (edge/core/hybrid) -> outputs + artifacts.
3) Telemetry captured (latency, success, user feedback).
4) Pattern miner detects repeated workflows -> proposes emergent skill.
5) Review gate -> approve/reject; if approved, stored in registry.
6) Optional promotion -> emergent skill becomes a God Skill after QA.

Pattern Miner (Emergent Skill Proposal)
---------------------------------------
Purpose:
- Detect repeated multi-step workflows and propose them as emergent skills.

Inputs:
- Recent execution traces (tool chain, inputs, outputs).
- User feedback and success signals.
- Context tags (project, tenant, channel).

Criteria (initial thresholds):
- Frequency: workflow seen >= 5 times in 14 days.
- Consistency: >= 80% success rate across runs.
- Stability: steps and parameters match within tolerance.
- Value: measurable time saved or repeated user intent.

Output:
- Candidate skill blueprint with:
  - trigger patterns
  - required inputs
  - step graph (tool chain)
  - guardrails (preconditions, approvals)

Review Gate:
- Human approval required before enabling.
- Auto-rollback if failure rate exceeds 20% in first 50 runs.

Emergent Skills Technical Spec (API + DB)
-----------------------------------------
API (Core):
- POST /skills/emergent/propose
  - body: { name, triggers[], inputs_schema, steps[], guardrails, metadata }
- GET /skills/emergent?status=pending|approved|rejected
- POST /skills/emergent/{id}/approve
- POST /skills/emergent/{id}/reject
- POST /skills/emergent/{id}/rollback
- POST /skills/emergent/{id}/promote

DB (Core, tenant-isolated):
Table: emergent_skill_candidates
- id (uuid, pk)
- tenant_id (uuid, indexed)
- status (pending|approved|rejected|rolled_back|promoted)
- name (text)
- triggers (json)
- inputs_schema (json)
- steps (json)
- guardrails (json)
- metrics (json) -- success_rate, avg_latency, runs, confidence
- source_trace_ids (json)
- created_at, updated_at
- approved_by (uuid), approved_at
- version (text)

Table: emergent_skill_runs
- id (uuid, pk)
- tenant_id (uuid, indexed)
- skill_id (uuid, indexed)
- status (success|failed)
- latency_ms (int)
- feedback (int) -- optional rating
- created_at

Table: skill_registry
- id (uuid, pk)
- tenant_id (uuid, indexed)
- type (god|emergent)
- name (text)
- tool_schema (json)
- policy (json) -- enabled, edge_only, requires_api, requires_device
- version (text)
- created_at, updated_at

Notes:
- All rows protected by RLS on tenant_id.
- Guardrails enforce approval before enablement.
- Rollback flips status and disables policy in registry.

Flow Diagram (ASCII)
--------------------
User -> Router -> Skill Exec -> Telemetry -> Pattern Miner -> Review Gate
  |         |            |            |           |             |
  |         +---------> Registry <----+           +--> Approve?
  |                        |                          |
  +------------------------+--------------------------+

Emergent Skill Example (JSON)
-----------------------------
```json
{
  "name": "weekly_status_digest",
  "triggers": [
    "weekly status",
    "riepilogo settimanale",
    "send weekly update"
  ],
  "inputs_schema": {
    "type": "object",
    "properties": {
      "recipient": { "type": "string" },
      "project": { "type": "string" },
      "week_start": { "type": "string" }
    },
    "required": ["recipient", "project"]
  },
  "steps": [
    { "tool": "rag_search", "args": { "query": "{{project}} status {{week_start}}" } },
    { "tool": "email_list", "args": { "account": "work", "limit": 50 } },
    { "tool": "summary_generate", "args": { "style": "exec", "max_tokens": 300 } },
    { "tool": "email_send", "args": { "to": "{{recipient}}", "subject": "Weekly status: {{project}}" } }
  ],
  "guardrails": {
    "requires_approval": true,
    "max_cost_usd": 0.25,
    "allowed_channels": ["email"],
    "rate_limit_per_day": 2
  },
  "metadata": {
    "source": "pattern_miner",
    "confidence": 0.87
  }
}
```

RAG Unification
---------------
Target pipeline:
1) Ingest -> chunk -> embed -> store
2) Retrieval: vector search + BM25
3) Fusion: RRF
4) Reranking: ColBERT/late-interaction (primary)

Storage:
- Qdrant for vectors (EU region).
- Postgres (or SQLite-vec for edge) for BM25 and metadata.
- Multi-tenant isolation: collection or partition per tenant.

API:
- /rag/ingest
- /rag/search (hybrid)
- /rag/context (formatted context for LLM)

Digital Twin (Voice + 3D Avatar)
--------------------------------
Capabilities:
- Voice cloning (opt-in) with real-time TTS for LORENZ responses.
- 3D avatar interaction with lip-sync and expressive gestures.
- Live session mode for real-time dialog (streaming input/output).

Architecture:
- Core handles identity, consent, voiceprint storage, and model selection.
- Edge gateway streams audio/viseme events to avatar clients (web/app).
- Real-time transport via WebRTC or WebSocket (decision pending).
- Voice cloning provider: Eleven Labs in phase 1, in-house in phase 2.
- Avatar stack: prototype both WebGL/Three + WebRTC + viseme streaming and MetaHuman.

API (proposed):
- /twin/voice/clone (enroll voice, opt-in consent required)
- /twin/voice/synthesize (stream TTS)
- /twin/avatar/session (create/join real-time avatar session)

Safety and compliance:
- Explicit consent required before any voice cloning.
- Voiceprints stored encrypted in EU only.
- Clear revoke/delete flow for user-controlled removal.

Delivery:
- Initial support via web-based avatar client.
- Gateway provides a fallback non-cloned voice if twin is disabled.

Avatar Evaluation Checklist
---------------------------
- End-to-end latency (ASR + LLM + TTS + render) under 1.5s target.
- Lip-sync accuracy (viseme alignment vs audio) at 60fps.
- GPU cost per concurrent session and device compatibility.
- Session stability (drops, jitter, recovery).
- Integration effort with LORENZ gateway and session manager.

RSI (Recursive Self Improvement)
--------------------------------
Guarded loop with telemetry and offline evaluation:
- Signals: click-through, answer ratings, tool success, latency, rerank delta.
- Offline eval sets: fixed queries + expected answers + grounding checks.
- Model/router tuning: change vector/text weights, RRF k, rerank threshold.
- Release gates: shadow mode -> canary -> full rollout.
- Kill switch and rollback required for every RSI change.

Data Residency (EU)
-------------------
- All core services in EU region only.
- Enforce EU-only object storage, database, vector store, logs.
- Edge gateway can run anywhere, but any sync to core remains EU.

Channel Strategy
----------------
Phase 1 (MVP):
- Telegram
- WhatsApp

Phase 2:
- Teams
- Slack

Decision:
- WhatsApp Cloud API (official) for production reliability and support.

Security and Permissions
------------------------
- Tenant isolation at DB layer (RLS).
- Skill execution policy enforced by Core.
- Gateway executes only approved tools per tenant and per user.
- Secrets handled in core; gateway uses short-lived tokens.

Deployment Topology
-------------------
Core (EU):
- API: FastAPI or TS service
- Postgres
- Qdrant
- Object store
- Metrics/logs

Gateway (Edge):
- Node runtime
- Channel adapters
- Skill executor
- Local storage for device tools

Migration Plan (Phased)
-----------------------
Phase 0: Rebrand
- Rename CLI, config keys, UI labels to LORENZ.
- Ensure no external "clawdbot" exposure.

Phase 1: Gateway + Core link
- Gateway sends messages to Core for routing and RAG.
- Core exposes RAG API and skill registry API.
- Telegram + WhatsApp go-live.

Phase 2: Skill Unification
- Add adapters for LORENZ Python skills into tool registry.
- Enforce policy flags and permissions at Core.
- Ship Teams + Slack.

Phase 3: RSI
- Add eval harness + offline scoring.
- Implement tuning loop and rollback controls.

Phase 4: Digital Twin
- Voice cloning enrollment + streaming TTS.
- Real-time 3D avatar sessions with lip-sync.

Risks and Mitigations
---------------------
- Skill count explosion: use allowlists per tenant and skill tagging.
- Device-only skills: enforce edge-only policy, no core execution.
- Dual runtime complexity: define strict API boundaries and ownership.
- RAG drift: RSI requires offline eval and canary gating.
- Voice cloning risk: enforce consent, revocation, and audit logging.
- Realtime avatar cost: gate by plan and throttle session concurrency.

Open Decisions
--------------
- How much of Core stays Python vs TS (recommend: TS gateway, Python RAG).
- Real-time transport (WebRTC vs WebSocket).
