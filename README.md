# AI Hiring Pipeline

An AI-powered backend system for automated candidate screening, pipeline management, and recruiter dashboard. Built with **FastAPI**, **SQLite**, **Google Gemini LLM**, and **React**.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![React](https://img.shields.io/badge/React-18-blue)
![LLM](https://img.shields.io/badge/LLM-Gemini-orange)

---

## Features

### Task 1: Candidate Screening API with LLM Evaluation
- Accept candidate profiles (name, phone, skills, experience, location, pitch)
- Load role configs from JSON files with specific evaluation criteria
- **Real LLM evaluation** via Google Gemini — scores candidates 0-100 with detailed reasoning
- Returns structured response: eligibility, score, reasoning, constraint check results

### Task 2: Multi-Stage State Machine with Persistence
- **Stage 1 — Intake**: Candidate validated and de-duplicated (by phone + role)
- **Stage 2 — AI Screen**: LLM evaluation runs automatically; ineligible candidates rejected
- **Stage 3 — Decision Bucket**: Auto-bucketed by score:
  - ≥80: **Advance** (interview)
  - 50–79: **Hold** (recruiter review)
  - <50: **Reject** (with alternate role suggestions)
- Every stage transition logged with timestamp, reason, and trigger
- Full audit trail queryable via API

### Task 3: Recruiter Dashboard API
- `GET /dashboard/role/{role_id}` — Candidates grouped by bucket with scores
- `GET /dashboard/candidate/{phone}` — Full history across all roles
- `POST /dashboard/override` — Manual bucket override with mandatory reason + audit trail

### Frontend (React)
- Candidate application form with real-time AI evaluation results
- Recruiter dashboard with stats, bucket tables, and override modal
- Candidate history viewer with pipeline timeline visualization

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI |
| Database | SQLite (SQLAlchemy ORM) |
| LLM | Google Gemini API (gemini-2.0-flash) |
| Frontend | React + Vite |

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Google Gemini API key ([Get one free](https://aistudio.google.com/apikey))

### 1. Clone and setup backend

```bash
git clone <your-repo-url>
cd "AI Pipeline"

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your Gemini API key:
# GEMINI_API_KEY=your_actual_key_here
```

### 3. Start the backend

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will be at `http://localhost:5173`.

---

## API Endpoints

### Candidates
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/candidates/apply` | Submit application (triggers full pipeline) |
| GET | `/api/candidates/{phone}/status` | Get candidate status across all roles |

### Roles
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/roles` | List all available roles |
| GET | `/api/roles/{role_id}` | Get role config details |

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/role/{role_id}` | All candidates grouped by bucket |
| GET | `/dashboard/candidate/{phone}` | Full candidate history |
| POST | `/dashboard/override` | Override bucket (with audit) |

---

## Data Model

```
Candidate (phone = unique key)
  └── Application (1 per role per candidate)
        ├── StageTransition (audit trail)
        └── BucketOverride (recruiter overrides)
```

- **Candidate**: Identified by phone number, shared across roles
- **Application**: One per role, tracks pipeline state, LLM score, bucket
- **StageTransition**: Full audit trail of pipeline stage changes
- **BucketOverride**: Separate audit for recruiter overrides

---

## Role Configs

Role configs are JSON files in the `roles/` directory:

| Role | File | Min Exp | Key Skills |
|------|------|---------|------------|
| Senior Electromechanical Engineer | `senior_electromechanical_engineer.json` | 5 years | SolidWorks, PLC Programming, Circuit Design, MATLAB |
| Senior Quantity Surveyor | `senior_quantity_surveyor.json` | 7 years | Cost Estimation, BOQ Preparation, Contract Management, AutoCAD |

---

## LLM Prompt Design

The prompt (in `app/prompts/screening.py`) is carefully structured to:
1. Provide full role context (skills, experience, location, criteria)
2. Present candidate profile and pitch
3. Define scoring guidelines (0-100 with specific band descriptions)
4. Request JSON output with score, reasoning, eligibility, and assessments
5. Handle edge cases (JSON parsing failures, LLM errors) gracefully

---

## Testing with curl

See `curl_examples.sh` for 12 complete test scenarios covering:
1. List roles
2. Strong fit → Advance
3. Moderate fit → Hold
4. Weak fit → Reject
5. Multi-role application
6. Candidate history lookup
7. Dashboard queries
8. Bucket override
9. Duplicate rejection

---

## Project Structure

```
AI Pipeline/
├── app/
│   ├── main.py             # FastAPI app entry point
│   ├── config.py            # Environment config
│   ├── database.py          # SQLAlchemy setup
│   ├── models.py            # ORM models (4 tables)
│   ├── schemas.py           # Pydantic validation schemas
│   ├── routers/
│   │   ├── candidates.py    # Apply + status endpoints
│   │   ├── pipeline.py      # Role listing endpoints
│   │   └── dashboard.py     # Dashboard + override endpoints
│   ├── services/
│   │   ├── llm_service.py   # Gemini API integration
│   │   ├── pipeline_engine.py  # 3-stage state machine
│   │   └── role_config.py   # JSON config loader
│   └── prompts/
│       └── screening.py     # LLM prompt template
├── frontend/                # React + Vite
├── roles/                   # Role config JSONs
├── requirements.txt
├── curl_examples.sh
└── .env.example
```

---

## Key Design Decisions

1. **Phone as unique key**: Candidates are identified by phone across roles, but each application is independent
2. **Synchronous pipeline**: All 3 stages execute in a single request for simplicity and demo-ability
3. **SQLite**: Zero-config database — just clone and run. Easy to swap for Postgres
4. **Structured LLM output**: Prompt forces JSON response; parser handles markdown fencing and edge cases
5. **Audit trail**: Every state transition and override is permanently logged with timestamps
