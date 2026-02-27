# CampusIQ — AI-First Intelligent College ERP

> An autonomous, AI-powered campus management system that **predicts**, **adapts**, and **automates** — turning raw campus data into intelligent decisions through natural language.

![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![AI](https://img.shields.io/badge/AI-XGBoost%20%2B%20SHAP-purple)
![Stack](https://img.shields.io/badge/stack-React%20%2B%20FastAPI-orange)
![LLM](https://img.shields.io/badge/LLM-Google%20Gemini-blue)
![Deployment](https://img.shields.io/badge/deployment-single%20server-success)

---

## 🚀 Quick Start (Single Server)

**Both frontend and backend are now combined into ONE server!**

### Prerequisites
- **Google Gemini API Key** (FREE) - Get it here: https://aistudio.google.com/app/apikey
- Docker (for containerized deployment) OR Python 3.11+ and Node.js 18+

### Setup Steps

1. **Get your Gemini API key** (required for AI features):
   ```powershell
   # Visit: https://aistudio.google.com/app/apikey
   # Copy your API key
   ```

2. **Configure API key**:
   ```powershell
   # Edit .env file in project root
   notepad .env
   
   # Add your key:
   GEMINI_API_KEY=AIzaSy_YOUR_API_KEY_HERE
   ```

3. **Test API connection** (optional but recommended):
   ```powershell
   .\test_gemini_api.ps1
   ```

4. **Start the application**:
   ```powershell
   # Windows: Just run this!
   .\start_production.ps1

   # Or use Docker:
   docker-compose -f docker-compose.production.yml up --build
   ```

**Access everything on http://localhost:8000** 🎉

📖 See [QUICK_START.md](QUICK_START.md) for detailed instructions.  
🔑 See [GEMINI_API_SETUP.md](GEMINI_API_SETUP.md) for API configuration help.  
⚡ See [OPTIMIZATION_REPORT.md](OPTIMIZATION_REPORT.md) for performance details.

---

## What is CampusIQ?

CampusIQ is an **AI-first college ERP** that replaces form-driven campus management with intelligent, conversational automation. Users manage the entire system through natural language — the AI classifies intent, assesses risk, executes directly, and maintains a full audit trail.

### Key Capabilities

| Feature | Description |
|---|---|
| **Command Console** | NL message → intent extraction → risk classification → direct execution → rollback |
| **Governance Dashboard** | Admin oversight: live stats, risk distribution, full audit trail |
| **Grade Prediction** | XGBoost predicts exam grades 4–6 weeks ahead with SHAP explainability |
| **NLP CRUD Engine** | "Show all CSE students in semester 5" → instant database query |
| **Context-Aware Chatbot** | Gemini-powered assistant injecting live attendance, CGPA, and predictions into context |
| **Smart Attendance** | QR-based, time-limited, single-use, with anti-fraud validation |
| **Risk Alerts** | Auto-flags at-risk students for faculty and admin |

---

## Architecture

### Single Server Deployment (Production)

```
┌──────────────────────────────────────────────┐
│         Single Server (Port 8000)           │
│  ┌────────────────────────────────────────┐ │
│  │  FastAPI Backend (serves API + UI)     │ │
│  │  ├─ API Routes (/api/*)                │ │
│  │  ├─ AI/ML Pipeline (XGBoost + SHAP)    │ │
│  │  └─ Serves React Frontend (/)          │ │
│  └────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
              ↓                ↓
     ┌────────────────┐  ┌────────────┐
     │  PostgreSQL    │  │   Redis    │
     │  + Redis       │  │   Cache    │
     └────────────────┘  └────────────┘
              ↓
     ┌────────────────┐
     │  Gemini LLM    │
     │  (Single Key)  │
     └────────────────┘
```

### Development Mode (Optional)
```
┌─────────────────┐     ┌──────────────────┐     ┌───────────────────┐
│  React Frontend │────▶│  FastAPI Backend  │────▶│  AI/ML Pipeline   │
│  (Vite + SPA)   │     │  (REST API)       │     │  (XGBoost + SHAP) │
└─────────────────┘     └──────────────────┘     └───────────────────┘
    Port 5173                Port 8000
```

### AI Stack

| Component | Engine | Fallback |
|---|---|---|
| **Command Console** | Gemini (`gemini-2.0-flash`) — intent extraction + risk classification | Keyword-based planner |
| **NLP CRUD Engine** | Gemini — intent detection + entity extraction | Regex-based classifier |
| **AI Chatbot** | Gemini — context-aware conversational Q&A | Rule-based knowledge base |
| **Prediction Engine** | XGBoost + SHAP (local model, no API needed) | — |

All LLM calls route through `GeminiClient` — a single-key client with exponential backoff retry. If Gemini is unavailable, every AI feature gracefully falls back to keyword/rule-based logic so the ERP stays functional.

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, Vite 5, Recharts, Lucide Icons, React Router v6 |
| **Backend** | Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2 |
| **Database** | PostgreSQL 16, Redis 7 |
| **AI/ML** | XGBoost, SHAP, scikit-learn, pandas |
| **LLM** | Google Gemini (`gemini-2.0-flash`) via single API key |
| **DevOps** | Docker, Docker Compose |
| **Auth** | JWT (python-jose), PBKDF2-SHA256 (passlib) |

---

## Gemini API Key Setup

CampusIQ uses Google Gemini exclusively for all LLM features. You need one API key.

### Get a free key

1. Go to **https://aistudio.google.com/app/apikey**
2. Sign in with a Google account
3. Click **Create API key** → copy it

Free tier gives 15 requests/minute and 1 million tokens/day — enough for development and demos.

### Configuration

CampusIQ uses a single Gemini API key for all AI features. Set it in your `.env`:

```env
GEMINI_API_KEY=AIza...your-key-here
```

The client includes automatic retry with exponential backoff. Free tier gives 15 requests/minute — enough for development and demos.

---

## Quick Start

### Option 1: Docker Compose (Recommended)

**Step 1 — Set your API key**

```bash
cd project-expo/backend
cp .env.example .env
```

Open `.env` and set:
```env
GEMINI_API_KEY=AIza...your-key-here
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
# Edit .env — set GEMINI_API_KEY at minimum (see Key Setup section above)

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
2. **AI parsing** — Gemini extracts intent, entity, and filters (falls back to keyword parsing if Gemini is unavailable)
3. **Risk classification** — every action is rated LOW / MEDIUM / HIGH based on operation type and affected record count
4. **Direct execution** — all operations execute immediately with RBAC enforcement, no approval gates
5. **Rollback support** — every write operation captures before/after state for one-click undo
6. **Audit trail** — every action (whether executed or failed) is logged immutably

The **Governance Dashboard** (`/governance`, admin only) shows live operation stats, risk distribution, and the full audit trail with risk/module/operation filters.

---

## Project Structure

```
project-expo/
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── CopilotPanel.jsx         # Command Console (NL → Execute → Result)
│       │   ├── GovernanceDashboard.jsx  # Admin oversight + audit trail
│       │   ├── StudentDashboard.jsx
│       │   ├── FacultyConsole.jsx
│       │   ├── AdminPanel.jsx
│       │   ├── FinanceManagement.jsx
│       │   ├── HRManagement.jsx
│       │   └── Timetable.jsx
│       ├── components/
│       │   ├── ChatWidget.jsx           # Floating Gemini chatbot
│       │   └── Sidebar.jsx              # Navigation sidebar
│       └── services/api.js              # All API methods
│
├── backend/
│   ├── app/
│   │   ├── services/
│   │   │   ├── gemini_pool_service.py   # Single-key Gemini client: ask_json + ask
│   │   │   ├── nlp_crud_service.py      # Intent detection + CRUD execution
│   │   │   ├── chatbot_service.py       # Context-aware Gemini chat
│   │   │   ├── conversational_ops_service.py  # Direct-execution AI ops + audit
│   │   │   ├── attendance_service.py
│   │   │   └── prediction_service.py
│   │   ├── api/routes/
│   │   │   ├── operational_ai.py        # /ops-ai/* endpoints
│   │   │   ├── copilot.py               # Legacy compatibility
│   │   │   └── chatbot.py
│   │   ├── models/models.py
│   │   ├── core/config.py               # Single Gemini key config
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
- Verify `GEMINI_API_KEY` is set correctly in `.env`
- Check the key is active at https://aistudio.google.com/app/apikey
- Check backend logs: `docker-compose logs backend` — look for `GeminiError`

**Rate limit errors (`429`) during heavy use:**
- Free tier: 15 RPM per key — wait 60 seconds for quota reset
- The client has automatic retry with exponential backoff

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
