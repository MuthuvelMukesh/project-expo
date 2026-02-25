# 🎓 CampusIQ — AI-First Intelligent College ERP

> An autonomous, AI-powered campus management system that **predicts**, **adapts**, and **automates** — turning raw campus data into intelligent decisions.

![Status](https://img.shields.io/badge/status-hackathon%20MVP-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![AI](https://img.shields.io/badge/AI-XGBoost%20%2B%20SHAP-purple)
![Stack](https://img.shields.io/badge/stack-React%20%2B%20FastAPI-orange)
![LLM](https://img.shields.io/badge/LLM-Gemma%20via%20Ollama-teal)

---

## 🚀 What is CampusIQ?

CampusIQ is an **AI-first college ERP** that replaces reactive, manual campus management with intelligent, predictive automation. Unlike traditional ERPs that simply store data, CampusIQ **learns from it** — predicting student outcomes, flagging at-risk students, automating attendance, and powering a natural-language AI Copilot that lets users manage the entire system through conversation.

### Key Innovations

| Feature | What Makes It Different |
|---|---|
| 🤖 **AI Copilot** | Natural language operations — manage the entire ERP through conversation |
| 🔮 **Grade Prediction** | XGBoost predicts exam grades 4–6 weeks before exams |
| 📅 **AI Timetable** | Intelligent schedule viewer with course details and faculty info |
| 💬 **NLP CRUD Engine** | "Show all CSE students in semester 5" → instant database query |
| 📊 **Explainable AI** | Every prediction shows _why_ via SHAP factor analysis |
| ✅ **Smart Attendance** | QR-based, time-limited, with anti-fraud validation |
| 🎯 **Risk Alerts** | Auto-flags at-risk students for faculty and admin |
| 🌗 **Theme Toggle** | Dark/light mode with localStorage persistence |
| 🔒 **Security-First** | PBKDF2-SHA256 hashing, no-leak error handling, and 100% on-premise |

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌───────────────────┐
│  React Frontend │────▶│  FastAPI Backend  │────▶│  AI/ML Pipeline   │
│  (Vite + SPA)   │     │  (REST API)       │     │  (XGBoost + SHAP) │
└─────────────────┘     └──────────────────┘     └───────────────────┘
                                │                        │
                         ┌──────┴──────┐          ┌──────┴──────┐
                         │ PostgreSQL  │          │ Ollama LLM  │
                         │ + Redis     │          │ (Gemma 2B)  │
                         └─────────────┘          └─────────────┘
```

### AI Stack

| Component | Role | Fallback |
|---|---|---|
| **AI Copilot** | Multi-step action planning from natural language | Keyword-based planner |
| **NLP CRUD Engine** | Intent detection + entity extraction for DB ops | Regex-based classifier |
| **AI Chatbot** | Context-aware Q&A using live student/faculty data | Rule-based knowledge base |
| **Prediction Engine** | XGBoost grade prediction + SHAP explainability | — |

> All AI features use the **Ollama** local LLM (default: `gemma:2b`). The chatbot is now **context-aware**, automatically injecting user data (attendance, CGPA, predictions) into prompts for personalized advice.

**Full architecture**: [CAMPUSIQ_ARCHITECTURE.md](./CAMPUSIQ_ARCHITECTURE.md)

---

## 📦 Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, Vite 5, Recharts, Lucide Icons, React Router v6 |
| **Backend** | Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2 |
| **Database** | PostgreSQL 16, Redis 7 (caching) |
| **AI/ML** | XGBoost, SHAP, scikit-learn, pandas, numpy |
| **LLM** | Ollama (Gemma 2B / 7B / 9B), httpx |
| **DevOps** | Docker, Docker Compose |
| **Auth** | JWT (python-jose), PBKDF2-SHA256 (passlib) |

---

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
git clone https://github.com/MuthuvelMukesh/project-expo.git
cd project-expo
docker-compose up -d
```

This starts **5 services**: PostgreSQL, Redis, Backend API, Frontend, and Ollama LLM.  
The backend auto-seeds demo data and the ML model is pre-trained at build time.

### Option 2: Local Development

```bash
# 1. Start PostgreSQL & Redis (via Docker or local install)
docker-compose up -d db redis

# 2. Backend
cd backend
cp .env.example .env                 # configure environment
python -m venv venv
venv\Scripts\activate                # Windows
pip install -r requirements.txt

# Train ML model
python -m app.ml.seed_data           # generate synthetic training CSV
python -m app.ml.train               # train XGBoost → saves .joblib

# Seed database & start server
python -m app.seed                   # populate PostgreSQL with demo data (Timetable, Users, etc.)
uvicorn app.main:app --reload        # http://localhost:8000

# 3. Frontend (new terminal)
cd frontend
npm install
npm run dev                          # http://localhost:5173

# 4. Ollama (optional — for AI features)
ollama pull gemma:2b                 # or gemma2:9b for better accuracy
ollama serve                         # http://localhost:11434
```

### 🔑 Demo Accounts

| Role | Email | Password |
|---|---|---|
| 🔑 Admin | `admin@campusiq.edu` | `admin123` |
| 👨‍🏫 Faculty | `faculty1@campusiq.edu` | `faculty123` |
| 👨‍🎓 Student | `student1@campusiq.edu` | `student123` |

### Access Points

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

### Frontend API Proxy

- Frontend API base path is `/api`.
- Vite dev server proxies `/api` using `VITE_API_PROXY_TARGET` (default: `http://localhost:8000`).
- In Docker Compose, `VITE_API_PROXY_TARGET` is set to `http://backend:8000`.

---

## 📂 Project Structure

```
project-expo/
├── frontend/                        # React + Vite SPA
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar.jsx          # Role-based nav + NotificationBell + ThemeToggle
│   │   │   ├── ChatWidget.jsx       # Floating AI chatbot (Context-Aware)
│   │   │   ├── NotificationBell.jsx # Dropdown notifications with unread badge
│   │   │   └── ThemeToggle.jsx      # Dark/light mode toggle
│   │   ├── pages/
│   │   │   ├── Login.jsx            # Auth page
│   │   │   ├── StudentDashboard.jsx # Student KPIs, predictions, attendance
│   │   │   ├── StudentProfile.jsx   # Profile editor + change password
│   │   │   ├── AttendanceDetails.jsx# Per-course breakdown + heatmap calendar
│   │   │   ├── FacultyConsole.jsx   # Course analytics + risk roster + QR
│   │   │   ├── AdminPanel.jsx       # Campus-wide KPIs + department analytics
│   │   │   ├── Timetable.jsx        # NEW: Visual schedule viewer
│   │   │   └── CopilotPanel.jsx     # AI Copilot natural language interface
│   │   ├── context/AuthContext.jsx  # JWT auth state
│   │   ├── services/api.js          # 60+ API methods
│   │   ├── App.jsx                  # Router + auth guards
│   │   └── index.css                # Design system (dark + light themes)
│   ├── package.json
│   └── Dockerfile
├── backend/                         # FastAPI + Python
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── auth.py          # Register, login, password reset/change
│   │   │   │   ├── students.py      # Dashboard, profile, attendance details
│   │   │   │   ├── faculty.py       # Courses, risk roster
│   │   │   │   ├── attendance.py    # QR generate/mark, analytics
│   │   │   │   ├── predictions.py   # Individual + batch predictions
│   │   │   │   ├── chatbot.py       # AI chatbot queries
│   │   │   │   ├── copilot.py       # AI Copilot plan/execute/history
│   │   │   │   ├── timetable.py     # NEW: Timetable management
│   │   │   │   └── notifications.py # System-wide alerts
│   │   │   └── dependencies.py      # JWT auth + role guards
│   │   ├── models/models.py         # SQLAlchemy ORM (10 models)
│   │   ├── schemas/schemas.py       # Pydantic v2 (50+ schemas)
│   │   ├── services/
│   │   │   ├── auth_service.py      # Registration + profile logic
│   │   │   ├── attendance_service.py# Attendance tracking
│   │   │   ├── prediction_service.py# AI grade predictions
│   │   │   ├── chatbot_service.py   # Context-aware LLM engine
│   │   │   ├── copilot_service.py   # Multi-step action planner
│   │   │   └── nlp_crud_service.py  # NL → Data translation
│   │   ├── ml/                      # Seed data, training, prediction logic
│   │   ├── core/                    # Config, security, database
│   │   ├── seed.py                  # Demo data seeder (incl. Timetables)
│   │   └── main.py                  # FastAPI app entry
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── docker-compose.yml               # Multi-container setup
├── CAMPUSIQ_ARCHITECTURE.md
└── README.md
```

---

## 🧠 Core Modules

### 1. 🤖 AI Copilot
Natural language interface for deep ERP management. Supports thousands of command variations through a multi-step action planner with Human-in-the-Loop confirmations.

### 2. 💬 Context-Aware AI Chatbot (IMPROVED)
The chatbot now automatically understands *who* is asking. It injects live student attendance, CGPA, and grade predictions (or faculty designations/courses) directly into the LLM context to provide personalized academic advice.

### 3. 📅 AI-Powered Timetable (NEW)
A visual, interactive schedule viewer for students and faculty. Displays daily class timings, course codes, room numbers (simulated), and faculty details. Integrated with the attendance system.

### 4. 🛡️ Security & Reliability (IMPROVED)
- **Hardened Auth**: Replaced truncated bcrypt hashing with full PBKDF2-SHA256.
- **Robust Routing**: NLP CRUD engine now uses precise regex-based intent classification.
- **Fail-Safe Processing**: Comprehensive audit fixed 10+ core issues including database session commits and runtime edge cases.

### 5. 🔮 Performance Prediction Engine
XGBoost model predicting final grades with SHAP factors. Automatically flags "At-Risk" students (below 65% attendance or predicted Fail/D grade).

---

## 🔌 New API Endpoints

### Timetable
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/timetable/student` | Get current student's timetable | Student |
| GET | `/api/timetable/faculty` | Get current faculty timetable | Faculty |
| POST | `/api/timetable/` | Create one timetable slot | Admin |
| DELETE | `/api/timetable/{slot_id}` | Delete a timetable slot | Admin |

---

## 👥 Team & Development

- **Project**: CampusIQ — AI-First Intelligent College ERP
- **Hackathon**: Project Expo MVP
- **Technology**: Built with a focus on **On-Premise AI** to ensure data privacy in educational institutions.

---

## 📄 License

This project is licensed under the MIT License.

---

> **CampusIQ** — _Because a college shouldn't need 100 humans to do what intelligent software can do in seconds._

