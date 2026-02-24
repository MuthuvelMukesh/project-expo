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
| 💬 **NLP CRUD Engine** | "Show all CSE students in semester 5" → instant database query |
| 📊 **Explainable AI** | Every prediction shows _why_ via SHAP factor analysis |
| ✅ **Smart Attendance** | QR-based, time-limited, with anti-fraud validation |
| 🎯 **Risk Alerts** | Auto-flags at-risk students for faculty and admin |
| 🔔 **Notification System** | Real-time bell alerts for attendance, predictions, and system events |
| 🌗 **Theme Toggle** | Dark/light mode with localStorage persistence |
| 🔒 **Privacy-First** | 100% on-premise — no student data leaves the campus |

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
| **NLP CRUD Engine** | Intent detection + entity extraction for DB ops | Keyword classifier |
| **AI Chatbot** | Conversational Q&A about academics | Rule-based knowledge base |
| **Prediction Engine** | XGBoost grade prediction + SHAP explainability | — |

> All AI features use the **Ollama** local LLM (default: `gemma:2b`). Upgrade to `gemma2:9b` in `.env` for better accuracy. Every AI function includes a **keyword fallback** so the app works even without a running LLM.

**Full architecture**: [CAMPUSIQ_ARCHITECTURE.md](./CAMPUSIQ_ARCHITECTURE.md)

---

## 📦 Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, Vite 5, Recharts, Lucide Icons, React Router v6 |
| **Backend** | Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2 |
| **Database** | PostgreSQL 16, Redis 7 |
| **AI/ML** | XGBoost, SHAP, scikit-learn, pandas, numpy |
| **LLM** | Ollama (Gemma 2B / 7B / 9B), httpx |
| **DevOps** | Docker, Docker Compose |
| **Auth** | JWT (python-jose), bcrypt (passlib) |

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
python -m app.seed                   # populate PostgreSQL with demo data
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

---

## 📂 Project Structure

```
project-expo/
├── frontend/                        # React + Vite SPA
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar.jsx          # Role-based nav + NotificationBell + ThemeToggle
│   │   │   ├── ChatWidget.jsx       # Floating AI chatbot
│   │   │   ├── NotificationBell.jsx # Dropdown notifications with unread badge
│   │   │   └── ThemeToggle.jsx      # Dark/light mode toggle
│   │   ├── pages/
│   │   │   ├── Login.jsx            # Auth page
│   │   │   ├── StudentDashboard.jsx # Student KPIs, predictions, attendance
│   │   │   ├── StudentProfile.jsx   # Profile editor + change password
│   │   │   ├── AttendanceDetails.jsx# Per-course breakdown + heatmap calendar
│   │   │   ├── FacultyConsole.jsx   # Course analytics + risk roster + QR
│   │   │   ├── AdminPanel.jsx       # Campus-wide KPIs + department analytics
│   │   │   ├── UserManagement.jsx   # CRUD users (admin only)
│   │   │   ├── CourseManagement.jsx # CRUD courses (admin only)
│   │   │   ├── DepartmentManagement.jsx # CRUD departments (admin only)
│   │   │   └── CopilotPanel.jsx     # AI Copilot natural language interface
│   │   ├── context/AuthContext.jsx  # JWT auth state
│   │   ├── services/api.js          # 50+ API methods
│   │   ├── App.jsx                  # Router + auth guards (10 routes)
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
│   │   │   │   ├── users.py         # User management CRUD
│   │   │   │   ├── courses.py       # Course management CRUD
│   │   │   │   ├── departments.py   # Department management CRUD
│   │   │   │   ├── notifications.py # Notification system
│   │   │   │   ├── export.py        # CSV data exports
│   │   │   │   └── admin.py         # Admin dashboard KPIs
│   │   │   └── dependencies.py      # JWT auth + role guards
│   │   ├── models/models.py         # SQLAlchemy ORM (8 models)
│   │   ├── schemas/schemas.py       # Pydantic v2 (40+ schemas)
│   │   ├── services/
│   │   │   ├── auth_service.py      # Registration + auto-profile creation
│   │   │   ├── attendance_service.py# Attendance logic
│   │   │   ├── prediction_service.py# AI predictions + recommendations
│   │   │   ├── chatbot_service.py   # LLM chat + rule fallback
│   │   │   ├── copilot_service.py   # Multi-step action planner + HITL
│   │   │   └── nlp_crud_service.py  # NL → SQL query engine
│   │   ├── ml/
│   │   │   ├── seed_data.py         # Synthetic data generator (500 students)
│   │   │   ├── features.py          # 12-feature engineering schema
│   │   │   ├── train.py             # XGBoost training pipeline
│   │   │   └── predict.py           # Inference + SHAP explainability
│   │   ├── core/                    # config, security, database
│   │   ├── seed.py                  # Demo data seeder
│   │   └── main.py                  # FastAPI app (13 route modules)
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── docker-compose.yml               # 5-service orchestration
├── CAMPUSIQ_ARCHITECTURE.md
└── README.md
```

---

## 🧠 Core Modules

### 1. 🤖 AI Copilot (NEW)
Natural language interface to manage the entire ERP. Users type commands like:
- *"Show all students in Computer Science with CGPA above 8"*
- *"Create a new course CS501 Database Systems for semester 5"*
- *"Delete inactive users"*

**Features**: Role-based capability matrix, risk classification (safe/low/high), human-in-the-loop confirmation for destructive operations, full audit trail via `ActionLog`.

### 2. 💬 NLP CRUD Engine (NEW)
Translates natural language into safe database queries. Supports READ, CREATE, UPDATE, DELETE, and ANALYZE intents across 7 entity types (students, faculty, courses, departments, attendance, predictions, users). Includes aggregation functions (count, average, group_by).

### 3. 🔮 Performance Prediction Engine
XGBoost regression model predicting final grades from 12 features (attendance, assignments, quizzes, labs, CGPA, etc.). Every prediction includes SHAP explanations showing *which factors* contribute most.

### 4. 💬 AI Campus Chatbot
Local LLM (Ollama + Gemma) for conversational Q&A. Integrates with NLP CRUD engine for live data queries. Rule-based fallback ensures 100% response rate even without GPU.

### 5. 📊 Student Intelligence Dashboard
Personalized view: KPI cards, attendance progress bars, Recharts visualizations, AI grade predictions table, and actionable recommendations.

### 6. 📈 Faculty Analytics Console
Class-level analytics: course selector, risk distribution pie chart, risk score bar chart, sortable student roster with SHAP factors, and QR attendance generation.

### 7. ✅ Smart Attendance System
Time-limited QR codes (default 90s), single-use tokens, anti-fraud validation, per-course analytics, and detailed attendance heatmap calendar.

### 8. 🛡️ Admin Automation Panel
Campus-wide KPIs, department comparison charts (attendance vs risk), AI-generated alerts (critical/warning/info), plus full CRUD management for users, courses, and departments.

### 9. 🔔 Notification System (NEW)
Real-time notification bell with unread badge, categorized alerts (attendance, prediction, copilot, system), mark-as-read, and 30-second auto-refresh.

### 10. 🌗 Theme System (NEW)
Dark/light mode toggle with `localStorage` persistence. Full CSS variable override system — every color, shadow, and gradient adapts to the selected theme.

---

## 🤖 ML Pipeline

```
seed_data.py → features.py → train.py → predict.py
     │               │            │           │
  500 students   12 features   XGBoost    SHAP factors
  ~3500 records  grade/risk    R², MAE    confidence
                 converters    accuracy   batch predict
```

**To retrain the model:**
```bash
cd backend
python -m app.ml.seed_data    # regenerate training data
python -m app.ml.train         # retrain + evaluate + save
python -m app.ml.predict       # quick test with 3 profiles
```

---

## 🔌 API Endpoints

### Authentication & Account
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/auth/register` | Register new user (auto-creates student/faculty profile) | — |
| POST | `/api/auth/login` | Login → JWT token | — |
| GET | `/api/auth/me` | Current user profile | ✅ |
| POST | `/api/auth/forgot-password` | Generate password reset token | — |
| POST | `/api/auth/reset-password` | Reset password with token | — |
| PUT | `/api/auth/change-password` | Change password (authenticated) | ✅ |

### Student
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/students/me/dashboard` | Student dashboard data | Student |
| GET | `/api/students/me/profile` | Student profile with department | Student |
| PUT | `/api/students/me/profile` | Update own profile | Student |
| GET | `/api/students/me/attendance` | Attendance summary | Student |
| GET | `/api/students/me/attendance/details` | Per-course, per-date breakdown | Student |
| GET | `/api/students/me/predictions` | AI predictions | Student |

### Faculty
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/faculty/me/courses` | Faculty courses | Faculty |
| GET | `/api/faculty/course/{id}/risk-roster` | Student risk roster | Faculty |

### Attendance
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/attendance/generate-qr` | Generate QR code | Faculty |
| POST | `/api/attendance/mark` | Mark attendance via QR | Student |
| GET | `/api/attendance/analytics/{id}` | Course analytics | Faculty/Admin |

### Predictions
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/predictions/{student_id}` | Student predictions | Faculty/Admin |
| GET | `/api/predictions/course/{id}/batch` | Batch predictions | Faculty/Admin |

### AI Features
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/chatbot/query` | AI chatbot query | ✅ |
| POST | `/api/copilot/plan` | Create AI action plan | ✅ |
| POST | `/api/copilot/execute` | Execute confirmed actions | ✅ |
| GET | `/api/copilot/history` | Copilot action audit log | ✅ |

### Admin Management
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/admin/dashboard` | Campus-wide KPIs | Admin |
| GET/POST/PUT/DELETE | `/api/users/` | User CRUD + profile management | Admin |
| GET/POST/PUT/DELETE | `/api/courses/` | Course management | Admin |
| GET/POST/PUT/DELETE | `/api/departments/` | Department management | Admin |

### System
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/notifications/` | User notifications | ✅ |
| GET | `/api/notifications/count` | Unread count | ✅ |
| PUT | `/api/notifications/read-all` | Mark all read | ✅ |
| GET | `/api/export/students` | CSV student export | Admin |
| GET | `/api/export/attendance/{id}` | CSV attendance export | Faculty/Admin |
| GET | `/api/export/risk-roster/{id}` | CSV risk roster export | Faculty/Admin |

---

## 🔧 Configuration

Key environment variables (see `.env.example`):

```env
# Database
DATABASE_URL=postgresql+asyncpg://campusiq:campusiq_secret@localhost:5432/campusiq

# JWT
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=60

# LLM (Ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma:2b          # Options: gemma:2b, gemma:7b, gemma2:9b
```

### LLM Model Options

| Model | RAM | Accuracy | Best For |
|---|---|---|---|
| `gemma:2b` | ~2 GB | Good | Demo, low-resource machines |
| `gemma:7b` | ~6 GB | Better | Development, testing |
| `gemma2:9b` | ~8 GB | Excellent | Production, complex queries |

---

## 👥 Team

- **Project**: CampusIQ
- **Type**: Hackathon Project — Project Expo
- **Focus**: AI/ML Innovation in Education Technology

---

## 📄 License

This project is licensed under the MIT License — see [LICENSE](./LICENSE) for details.

---

> **CampusIQ** — _Because a college shouldn't need 100 humans to do what intelligent software can do in seconds._
