# 🎓 CampusIQ — AI-First Intelligent College ERP

> An autonomous, AI-powered campus management system that **predicts**, **adapts**, and **automates** — turning raw campus data into intelligent decisions.

![Status](https://img.shields.io/badge/status-hackathon%20MVP-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![AI](https://img.shields.io/badge/AI-XGBoost%20%2B%20SHAP-purple)
![Stack](https://img.shields.io/badge/stack-React%20%2B%20FastAPI-orange)

---

## 🚀 What is CampusIQ?

CampusIQ is an **AI-first college ERP** that replaces reactive, manual campus management with intelligent, predictive automation. Unlike traditional ERPs that simply store data, CampusIQ **learns from it** — predicting student outcomes, flagging at-risk students, automating attendance, and powering a campus-wide AI chatbot.

### Key Innovations

| Feature | What Makes It Different |
|---|---|
| 🔮 **Grade Prediction** | XGBoost predicts exam grades 4–6 weeks before exams |
| 🤖 **AI Chatbot** | Local LLM (Ollama) answers academic queries using live data |
| 📊 **Explainable AI** | Every prediction shows _why_ via SHAP factor analysis |
| ✅ **Smart Attendance** | QR-based, time-limited, with anti-fraud validation |
| 🎯 **Risk Alerts** | Auto-flags at-risk students for faculty and admin |
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

**Full architecture**: [CAMPUSIQ_ARCHITECTURE.md](./CAMPUSIQ_ARCHITECTURE.md)

---

## 📦 Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, Vite 5, Recharts, Lucide Icons, React Router v6 |
| **Backend** | Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2 |
| **Database** | PostgreSQL 16, Redis 7 |
| **AI/ML** | XGBoost, SHAP, scikit-learn, pandas, numpy |
| **LLM** | Ollama (Gemma 2B), LangChain |
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
├── frontend/                    # React + Vite SPA
│   ├── src/
│   │   ├── components/          # Sidebar, ChatWidget
│   │   ├── pages/               # Login, StudentDashboard, FacultyConsole, AdminPanel
│   │   ├── context/             # AuthContext (JWT)
│   │   ├── services/            # API client
│   │   ├── App.jsx              # Router + auth guards
│   │   └── index.css            # Design system (glassmorphism dark theme)
│   ├── package.json
│   └── Dockerfile
├── backend/                     # FastAPI + Python
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/          # auth, students, faculty, attendance, predictions, chatbot, admin
│   │   │   └── dependencies.py  # JWT auth + role guards
│   │   ├── models/models.py     # SQLAlchemy ORM (User, Student, Faculty, Course, Attendance, Prediction)
│   │   ├── schemas/schemas.py   # Pydantic v2 request/response
│   │   ├── services/            # auth, attendance, prediction, chatbot
│   │   ├── ml/
│   │   │   ├── seed_data.py     # Synthetic data generator (500 students)
│   │   │   ├── features.py      # 12-feature engineering schema
│   │   │   ├── train.py         # XGBoost training pipeline
│   │   │   └── predict.py       # Inference + SHAP explainability
│   │   ├── core/                # config, security, database
│   │   ├── seed.py              # Demo data seeder
│   │   └── main.py              # FastAPI app entry point
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── docker-compose.yml           # 5-service orchestration
├── CAMPUSIQ_ARCHITECTURE.md     # Detailed architecture document
└── README.md
```

---

## 🧠 Core Modules

### 1. Performance Prediction Engine
XGBoost regression model predicting final grades from 12 features (attendance, assignments, quizzes, labs, CGPA, etc.). Every prediction includes SHAP explanations showing *which factors* contribute most.

### 2. AI Campus Chatbot
Local LLM (Ollama + Gemma 2B) with LangChain. Rule-based fallback ensures 100% response rate even without GPU. Contextual suggested actions guide conversations.

### 3. Student Intelligence Dashboard
Personalized view: KPI cards, attendance progress bars, Recharts visualizations, AI grade predictions table, and actionable recommendations.

### 4. Faculty Analytics Console
Class-level analytics: course selector, risk distribution pie chart, risk score bar chart, sortable student roster with SHAP factors, and QR attendance generation.

### 5. Smart Attendance System
Time-limited QR codes (default 90s), single-use tokens, anti-fraud validation, and per-course attendance analytics.

### 6. Admin Automation Panel
Campus-wide KPIs, department comparison charts (attendance vs risk), AI-generated alerts (critical/warning/info) based on department performance.

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

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/auth/register` | Register new user | — |
| POST | `/api/auth/login` | Login → JWT token | — |
| GET | `/api/auth/me` | Current user profile | ✅ |
| GET | `/api/students/me/dashboard` | Student dashboard data | Student |
| GET | `/api/students/me/attendance` | Attendance summary | Student |
| GET | `/api/students/me/predictions` | AI predictions | Student |
| POST | `/api/attendance/generate-qr` | Generate QR code | Faculty |
| POST | `/api/attendance/mark` | Mark attendance via QR | Student |
| GET | `/api/attendance/analytics/{id}` | Course analytics | Faculty/Admin |
| GET | `/api/faculty/me/courses` | Faculty courses | Faculty |
| GET | `/api/faculty/course/{id}/risk-roster` | Student risk roster | Faculty |
| GET | `/api/predictions/{student_id}` | Student predictions | Faculty/Admin |
| GET | `/api/predictions/course/{id}/batch` | Batch predictions | Faculty/Admin |
| POST | `/api/chatbot/query` | AI chatbot query | ✅ |
| GET | `/api/admin/dashboard` | Campus-wide KPIs | Admin |

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
