# CampusIQ — AI-First Intelligent College ERP

> An autonomous, AI-powered campus management system that **predicts**, **adapts**, and **automates** — turning raw campus data into intelligent decisions through natural language.

![Status](https://img.shields.io/badge/status-hackathon%20MVP-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![AI](https://img.shields.io/badge/AI-XGBoost%20%2B%20SHAP-purple)
![Stack](https://img.shields.io/badge/stack-React%20%2B%20FastAPI-orange)
![LLM](https://img.shields.io/badge/LLM-Google%20Gemini-blue)

---

## What is CampusIQ?

CampusIQ is an **AI-first college ERP** that replaces form-driven campus management with intelligent, conversational automation. Users manage the entire system through natural language — the AI classifies intent, assesses risk, enforces approval, executes securely, and maintains a full audit trail.

### Key Capabilities

| Feature | Description |
|---|---|
| **Command Console** | NL → structured plan → risk review → human-in-the-loop approval → execution → rollback |
| **Governance Dashboard** | Admin oversight: pending approvals, live stats, risk distribution, full audit trail |
| **Grade Prediction** | XGBoost predicts exam grades 4–6 weeks ahead with SHAP explainability |
| **NLP CRUD Engine** | "Show all CSE students in semester 5" → instant database query |
| **Context-Aware Chatbot** | Gemini-powered assistant injecting live attendance, CGPA, and predictions into context |
| **Smart Attendance** | QR-based, time-limited, single-use, with anti-fraud validation |
| **Risk Alerts** | Auto-flags at-risk students for faculty and admin |

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌───────────────────┐
│  React Frontend │────▶│  FastAPI Backend  │────▶│  AI/ML Pipeline   │
│  (Vite + SPA)   │     │  (REST API)       │     │  (XGBoost + SHAP) │
└─────────────────┘     └──────────────────┘     └───────────────────┘
                                │                        │
                         ┌──────┴──────┐          ┌──────┴──────┐
                         │ PostgreSQL  │          │   Gemini    │
                         │ + Redis     │          │ Key  Pool   │
                         └─────────────┘          └─────────────┘
```

### AI Stack

| Component | Engine | Fallback |
|---|---|---|
| **Command Console** | Gemini (`nlp` pool) — action planning + risk classification | Keyword-based planner |
| **NLP CRUD Engine** | Gemini (`nlp` pool) — intent detection + entity extraction | Regex-based classifier |
| **AI Chatbot** | Gemini (`chat` pool) — context-aware conversational Q&A | Rule-based knowledge base |
| **Prediction Engine** | XGBoost + SHAP (local model, no API needed) | — |

All LLM calls route through `GeminiPoolClient` — a module-isolated key pool with automatic retry/failover across keys. If Gemini is unavailable, every AI feature gracefully falls back to keyword/rule-based logic so the ERP stays functional.

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, Vite 5, Recharts, Lucide Icons, React Router v6 |
| **Backend** | Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2 |
| **Database** | PostgreSQL 16, Redis 7 |
| **AI/ML** | XGBoost, SHAP, scikit-learn, pandas |
| **LLM** | Google Gemini (`gemini-1.5-flash`) via per-module key pools |
| **DevOps** | Docker, Docker Compose |
| **Auth** | JWT (python-jose), PBKDF2-SHA256 (passlib) |

---

## Gemini API Key Setup

CampusIQ uses Google Gemini exclusively for all LLM features. You need at least one API key.

### Get a free key

1. Go to **https://aistudio.google.com/app/apikey**
2. Sign in with a Google account
3. Click **Create API key** → copy it

Free tier gives 15 requests/minute and 1 million tokens/day per key — enough for development and demos.

### How the key pool works

CampusIQ splits LLM calls across five isolated module pools:

| Pool variable | Used by |
|---|---|
| `GEMINI_NLP_KEYS` | Command Console planner + NLP CRUD engine |
| `GEMINI_CHAT_KEYS` | AI Chatbot |
| `GEMINI_PREDICTIONS_KEYS` | Grade prediction explanations |
| `GEMINI_FINANCE_KEYS` | Finance module queries |
| `GEMINI_HR_KEYS` | HR / payroll module queries |

**Each pool is a comma-separated list of keys.** When one key hits the rate limit, the next key in the list is tried automatically. If a pool is empty, the fallback `GOOGLE_API_KEY` is used.

**Minimum setup (1 key):**
```env
GOOGLE_API_KEY=AIza...your-key-here
```

**Recommended setup (2–3 keys for demo/presentation):**
```env
GOOGLE_API_KEY=AIza...key1          # primary fallback
GEMINI_NLP_KEYS=AIza...key1,AIza...key2,AIza...key3
GEMINI_CHAT_KEYS=AIza...key1,AIza...key2
```

Using separate keys per module means Command Console queries don't consume the chatbot's quota and vice versa — no request will ever fail from rate limiting during a demo.

---

## Quick Start

### Option 1: Docker Compose (Recommended)

**Step 1 — Set your API key**

```bash
cd project-expo/backend
cp .env.example .env
```

Open `.env` and set at minimum:
```env
GOOGLE_API_KEY=AIza...your-key-here
```

Optionally add more keys per module for better throughput:
```env
GEMINI_NLP_KEYS=AIza...key1,AIza...key2
GEMINI_CHAT_KEYS=AIza...key1,AIza...key2
```

**Step 2 — Start everything**

```bash
cd project-expo
docker-compose up -d
```

This starts **4 services**: PostgreSQL, Redis, Backend API, and React Frontend.

The backend automatically:
- Creates all database tables
- Seeds demo users, students, faculty, courses, departments, attendance, and predictions
- Trains the XGBoost ML model (at build time)

**Step 3 — Access the app**

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

---

### Option 2: Local Development

**Prerequisites:** Python 3.11+, Node.js 18+, PostgreSQL 16, Redis 7

**Step 1 — Infrastructure**

```bash
# Start only the databases (PostgreSQL + Redis)
docker-compose up -d db redis
```

**Step 2 — Backend**

```bash
cd backend

# Copy and configure environment
cp .env.example .env
# Edit .env — set GOOGLE_API_KEY at minimum (see Key Setup section above)

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Train the ML model (one-time setup)
python -m app.ml.seed_data       # generates synthetic training CSV
python -m app.ml.train           # trains XGBoost model → saves .joblib files

# Seed the database with demo data
python -m app.seed_db

# Start the API server
uvicorn app.main:app --reload    # runs at http://localhost:8000
```

**Step 3 — Frontend**

```bash
# Open a new terminal
cd frontend

npm install
npm run dev                      # runs at http://localhost:5173
```

---

## Demo Accounts

| Role | Email | Password | Access |
|---|---|---|---|
| Admin | `admin@campusiq.edu` | `admin123` | Full access + Command Console + Governance |
| Faculty | `faculty1@campusiq.edu` | `faculty123` | Courses, attendance, risk roster |
| Student | `student1@campusiq.edu` | `student123` | Dashboard, predictions, attendance |

---

## How the Command Console Works

1. **Type a natural language command** — e.g. *"Show all students in Computer Science with CGPA below 6"*
2. **AI planning** — Gemini parses intent, entity, and filters into a structured action plan (falls back to keyword parsing if Gemini is unavailable)
3. **Risk classification** — every action is rated LOW / MEDIUM / HIGH
   - `LOW` (READ, ANALYZE, NAVIGATE) → auto-executed instantly
   - `MEDIUM` (UPDATE) → shown to user with preview, requires confirmation
   - `HIGH` (CREATE, DELETE) → requires confirmation + optional 2FA
4. **Approval** — user reviews affected records, optionally selects per-record, confirms or rejects
5. **Execution** — action runs through the NLP CRUD engine with RBAC enforcement
6. **Audit trail** — every action (whether executed, rejected, or failed) is logged immutably

The **Governance Dashboard** (`/governance`, admin only) shows all pending approvals, live operation stats, and the full audit trail with risk/module/operation filters.

---

## Project Structure

```
project-expo/
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── CopilotPanel.jsx         # Command Console (NL → Plan → Execute)
│       │   ├── GovernanceDashboard.jsx  # Admin oversight + pending approvals
│       │   ├── StudentDashboard.jsx
│       │   ├── FacultyConsole.jsx
│       │   ├── AdminPanel.jsx
│       │   ├── FinanceManagement.jsx
│       │   ├── HRManagement.jsx
│       │   └── Timetable.jsx
│       ├── components/
│       │   ├── ChatWidget.jsx           # Floating Gemini chatbot
│       │   └── Sidebar.jsx              # Live pending approval badge
│       └── services/api.js              # All API methods
│
├── backend/
│   ├── app/
│   │   ├── services/
│   │   │   ├── gemini_pool_service.py   # Key pool: generate_json + generate_text
│   │   │   ├── copilot_service.py       # Action planning + risk classification
│   │   │   ├── nlp_crud_service.py      # Intent detection + CRUD execution
│   │   │   ├── chatbot_service.py       # Context-aware Gemini chat
│   │   │   ├── conversational_ops_service.py  # Ops AI core + audit
│   │   │   ├── attendance_service.py
│   │   │   └── prediction_service.py
│   │   ├── api/routes/
│   │   │   ├── operational_ai.py        # /ops-ai/* endpoints
│   │   │   ├── copilot.py
│   │   │   └── chatbot.py
│   │   ├── models/models.py
│   │   ├── core/config.py               # Gemini key pool config
│   │   └── seed_db.py
│   ├── .env.example
│   └── requirements.txt
│
├── docker-compose.yml
└── README.md
```

---

## Troubleshooting

**AI features return "no response" or use fallback:**
- Verify `GOOGLE_API_KEY` is set correctly in `.env`
- Check the key is active at https://aistudio.google.com/app/apikey
- Check backend logs: `docker-compose logs backend` — look for `GeminiPoolError`

**Rate limit errors (`429`) during heavy use:**
- Add 2–3 more keys to `GEMINI_NLP_KEYS` and `GEMINI_CHAT_KEYS` (comma-separated)
- Free tier: 15 RPM per key — 3 keys gives 45 RPM per module

**Database already seeded warning:**
- Normal on restart — the seeder is idempotent and skips if data exists

**Frontend cannot reach backend:**
- Ensure backend is running on port 8000
- Check `VITE_API_PROXY_TARGET` in docker-compose.yml or vite.config.js

**ML model not found error:**
- Run `python -m app.ml.seed_data && python -m app.ml.train` inside the backend directory

---

## License

MIT License — see LICENSE file.

---

> **CampusIQ** — _Because a college shouldn't need 100 humans to do what intelligent software can do in seconds._
