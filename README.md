# ⚖️NyayaSarthi

**Court Order Execution System — turning judicial directives into tracked, accountable administrative action.**

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688)
![React](https://img.shields.io/badge/React-Frontend-61DAFB)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-336791)
![Docker](https://img.shields.io/badge/Docker-Container-2496ED)

---

## Problem

Court judgments in India are published as long, dense PDFs. Government officials manually read 20+ pages to extract a handful of actionable directives — a process that is slow, error-prone, and completely untracked. There is no standardized system to capture, assign, monitor, or audit compliance with court orders, which leads to missed deadlines and even contempt-of-court proceedings.

| Problem | Impact |
|---|---|
| Time-consuming process | Officers spend hours parsing documents for a few actionable items |
| Error-prone interpretation | Critical compliance requirements buried in dense legal text are routinely missed |
| No standardised tracking | No mechanism exists to capture, assign, or monitor outcomes |
| Missed deadlines | Lack of tracking leads to contempt-of-court proceedings |
| Zero accountability | No audit trail to verify whether a court directive was ever acted upon |

## Vision

A unified national platform where no court order is ignored, no deadline is missed, and every government action is fully traceable — enabling efficient governance and institutional accountability across India.

**Product mission:** Convert unstructured judgment PDFs into structured, trackable, and accountable administrative workflows using OCR + NLP + LLM-based extraction, backed by a mandatory human-in-the-loop verification layer.

---

## How it works

```
PDF Upload
   │
   ▼
Document Type Detection (digital vs scanned)
   │
   ├─ Digital  → pdfplumber text/table extraction
   └─ Scanned  → OCR (Tesseract) → machine-readable text
   │
   ▼
AI Extraction (Google Gemini)
   - Case metadata (case no., court, parties, order date)
   - Directives: description, source page + snippet, relative deadline, suggested department
   │
   ▼
Deterministic Deadline Normalization (code, not LLM)
   "within 30 days" → absolute date, anchored to order date
   │
   ▼
Draft Persistence → status = pending_verification (never auto-approved)
   │
   ▼
AI Verification Queue (Legal Officer)
   Approve / Edit + Approve / Reject (with reason) — every directive, no bulk skip
   │
   ▼
Action Publication → live, tracked Actions routed to department
   │
   ▼
Deadline Monitoring (daily job) → approaching / overdue alerts
   │
   ▼
Actioned Dashboard (status, compliance %, filters, export)
   │
   ▼
Audit Trail (append-only log of every step, always retrievable)
```

**Non-negotiable rule:** AI output never auto-transitions to `approved`. It only ever creates `pending_verification` records — a human must approve, edit, or reject every single extracted directive before it becomes an official, tracked action.

---

## Key features

1. **Automated Judgment Understanding** — extracts key legal information from complex, multi-page PDFs (scanned or digital) in minutes.
2. **AI-Based Action Plan Generation** — converts court directives into clear, structured, actionable tasks.
3. **Accountability Engine** — intelligently assigns responsibility to specific departments and roles.
4. **Human-in-the-Loop Verification** — every AI output is reviewed and approved before it becomes official.
5. **Smart Deadline Tracking** — converts relative timelines ("within 30 days") into exact dates with proactive alerts.
6. **Audit Trail & Compliance Records** — tracks every action end-to-end for full transparency and accountability.

---

## Who it's for

- **Legal Officers** (in-house counsel) — fast triage of new judgments, deadline visibility, correct AI extraction before it goes live.
- **Administrative Authorities** — dashboard of all open directives across departments, escalation visibility, audit-ready reports.
- **Department Officers** — simple task list with deadlines, one-click status updates, reminders.
- **Oversight/Audit Bodies** — read-only audit views, exportable compliance records.

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React (JavaScript) + Tailwind CSS + Axios |
| Backend | Python, FastAPI (async) + Uvicorn |
| Database | PostgreSQL |
| AI / ML | Google Gemini (`google-generativeai`) — structured JSON extraction only, never final decisions |
| PDF parsing | `pdfplumber` (digital PDFs) |
| OCR | Tesseract (scanned PDFs — kept local for data sovereignty) |
| Auth | JWT-based sessions, role-based access control |
| Config | `.env` (python-dotenv) |
| Deployment | Docker / Docker Compose |

### High-level architecture

```
PDF Input
   │
   ▼
NyayaSarthi Core Processing Hub
   │
   ├──► OCR & Extraction Frame   (pdfplumber / OCR)
   ├──► Intelligence Frame       (Gemini: entities, directives, deadlines)
   └──► Output Frame             (validated structured JSON)
   │
   ▼
PostgreSQL
```

### Backend routers

`/auth` · `/cases` · `/upload` · `/extraction` · `/verification` · `/actions` · `/departments` · `/audit`

Every mutating endpoint writes a corresponding `audit_log` entry in the same DB transaction as the change — the audit trail can never drift from actual state.

---

## Data model (PostgreSQL)

```
users ──────────────< audit_log
  │                        ▲
  ▼                        │
departments ─────< actions >───── directives ──────< cases
```

| Table | Purpose |
|---|---|
| `users` | Accounts + role (`legal_officer`, `admin_authority`, `department_officer`, `auditor`) |
| `departments` | Department/role reference data, supports hierarchy |
| `cases` | One row per uploaded judgment; tracks status, source PDF hash (dedupe), order date |
| `directives` | AI-extracted draft items — description, source page/snippet, confidence, raw + computed deadline, suggested department, verification status |
| `actions` | Published, tracked items — created only from **approved** directives |
| `audit_log` | Append-only, insert-only — every state change, human or system |
| `alerts` | Deadline monitoring — approaching / overdue |

**Key integrity rules:**
- A directive can only produce an action once `verification_status IN ('approved','edited_approved')`.
- `actions.status = 'overdue'` is computed by a scheduled job, never manually settable (prevents gaming the compliance metric).
- `audit_log` is insert-only — no UPDATE/DELETE route is exposed.
- Case status transitions are one-directional (no case can jump straight from `uploaded` to `actioned`).

---

## Screens

```
Login
└── Case Processor (Home)
    ├── Process New Judgment → Case Intake (upload PDF)
    ├── AI Verification Queue (review every directive)
    ├── Approved Actions (confirmed items)
    ├── Actioned Dashboard (status, compliance %, filters, export)
    └── Audit Trail (read-only, per case)
```

**Design principles:** trust through transparency (every AI item links back to its source text), zero training required, verification-first (no bulk "approve all"), status at a glance (color-coded, never color-only), government-grade accessible design (WCAG AA).

---

## MVP scope

**In scope:** single-PDF upload (scanned or digital), OCR + extraction pipeline, LLM-based entity/directive/deadline extraction, department suggestion, human-in-the-loop verification queue, actioned dashboard, full audit log.

**Deferred to future phases:** multilingual (Hindi/regional) judgment processing, officer-level (individual) task assignment, predictive compliance risk scoring, integration with government systems (CCMS/CIS), SMS/push notifications, bulk/batch processing.

---

## Risks & mitigations

| Risk | Mitigation |
|---|---|
| LLM hallucinates a directive/deadline that doesn't exist | Mandatory human verification; source snippet shown alongside every extracted item |
| OCR fails on poor-quality scans | Fallback manual-entry path; confidence scoring |
| Officers distrust AI suggestions | UI shows extraction confidence + source citation |
| Sensitive case data breach | Encryption at rest/in transit, RBAC, audit logging from day one |
| Deadline miscalculation | Deadline math is deterministic (code), not LLM-generated; humans review every computed date |

---

## Getting started (local dev)

```bash
git clone <repo-url> nyayasarthi
cd nyayasarthi

# copy env template and fill in secrets
cp .env.example .env   # DATABASE_URL, GEMINI_API_KEY, JWT_SECRET, ENV

# spin up Postgres + backend + frontend
docker compose up --build
```

Backend: FastAPI + Uvicorn (`backend/`) · Frontend: React + Tailwind (`frontend/`) · DB: PostgreSQL, migrations via Alembic.

Health check: `GET /healthz`

---


## Disclaimer

NyayaSarthi's AI outputs are **draft suggestions only**. No legal liability is assumed by the system — all compliance decisions and sign-offs remain with the human officer.
