# CampusIQ Technical Codebase Reference

Generated on: **2026-02-27**

This document is an implementation-focused technical map of the `project-expo` repository, inferred from the current codebase (backend + frontend + deployment files).

---

## 1) Repository Overview

CampusIQ is an AI-first college ERP with:
- **Backend:** FastAPI + async SQLAlchemy + PostgreSQL + ML + LLM orchestration
- **Frontend:** React (Vite) role-based SPA
- **Deployment:** Docker Compose (dev split) + single-server production path
- **Primary domains:** academics, attendance, predictions, NLP CRUD, conversational operational AI, finance, HR

### Current scale snapshot
- `backend/app` Python files: **47**
- `backend/tests` Python files: **6**
- `frontend/src` JS/JSX files: **33**
- Root markdown docs: **11**

---

## 2) Top-Level Structure

- `backend/` — API, services, models, schemas, ML pipeline, seeds, tests
- `frontend/` — React SPA, pages/components/services/context
- Root docs/scripts — deployment, setup, optimization, security recovery, start/build scripts

Notable root files:
- `docker-compose.yml` (split dev stack)
- `docker-compose.production.yml` + `Dockerfile.production` (single-server production path)
- `README.md`, `QUICK_START.md`, `TECHNICAL_DOCUMENTATION.md`
- PowerShell/Bash helper scripts (`start_*`, `build_*`, `test_*`)

---

## 3) Backend Architecture

## 3.1 Entry Point and Lifecycle
- Entry: `backend/app/main.py`
- Creates FastAPI app, enables CORS, registers API routers, and optionally serves built frontend static assets.
- Lifespan shutdown closes shared HTTP clients (`close_http_client`) used by LLM integrations.

## 3.2 Core Runtime Modules
- `app/core/config.py`
  - Pydantic `BaseSettings` for app, DB, JWT, and Gemini configuration.
  - Single Gemini API key (`GEMINI_API_KEY`) with configurable model, temperature, and retry settings.
- `app/core/database.py`
  - Async SQLAlchemy engine and session factory.
  - Request-scoped `get_db()` dependency with commit/rollback handling.
- `app/core/security.py`
  - Password hashing: PBKDF2-SHA256 (`passlib`).
  - JWT create/decode via `python-jose`.

## 3.3 API Surface (Route Modules)
`backend/app/api/routes/` currently includes:
- `auth.py`
- `students.py`
- `faculty.py`
- `attendance.py`
- `predictions.py`
- `chatbot.py`
- `admin.py`
- `nlp_crud.py`
- `copilot.py`
- `users.py`
- `courses.py`
- `departments.py`
- `notifications.py`
- `export.py`
- `timetable.py`
- `finance.py`
- `hr.py`
- `operational_ai.py`

Mounted prefixes in `main.py` follow `/api/<module>` conventions.

## 3.4 Services Layer
`backend/app/services/` provides domain and AI orchestration logic, including:
- `auth_service.py` — registration/auth workflows
- `attendance_service.py` — attendance operations/analytics
- `prediction_service.py` — prediction APIs integrating ML inference
- `chatbot_service.py` — conversational responses with context
- `nlp_crud_service.py` — natural-language CRUD parsing and execution
- `conversational_ops_service.py` — **Intent → Permission → Execute → Audit** pipeline (no approval gates, no confirmation prompts, no 2FA)
- `gemini_pool_service.py` — LLM abstraction:
  - Single Google Gemini API key client (`GeminiClient`)
  - Methods: `ask_json()` for structured output, `ask()` for text
  - Exponential backoff retry with configurable attempts

## 3.5 Data Model (SQLAlchemy ORM)
Key entities in `app/models/models.py`:
- Identity/RBAC: `User`, `UserRole`
- Academic core: `Department`, `Student`, `Faculty`, `Course`, `Attendance`
- AI/ops governance: `Prediction`, `ActionLog`, Operational AI audit/execution models
- UX/system: `Notification`, `Timetable`
- Finance module: `FeeStructure`, `StudentFees`, `Invoice`, `Payment`, `StudentLedger`, `FeeWaiver`
- HR module: `Employee`, `SalaryStructure`, `SalaryRecord`, `EmployeeAttendance`

Database design style:
- Classical relational schema with FK relationships and JSON fields for AI payloads/explanations.
- Auditability emphasized for AI-assisted actions.

## 3.6 Authentication & Session Model
- Login endpoint sets JWT in **httpOnly cookie** (`access_token`).
- Frontend sends requests with `credentials: include`.
- `/auth/me` drives session restoration in frontend startup.
- Password reset currently uses in-memory reset token store (documented as demo-level behavior).

---

## 4) ML / Prediction Subsystem

Location: `backend/app/ml/`
- `train.py`: XGBoost training pipeline
  - train/test split, metrics (MAE/RMSE/R²), cross-validation, feature importance
  - outputs `grade_predictor.joblib` + metadata JSON
- `predict.py`: inference and explainability
  - loads cached model singleton
  - predicts score/grade/risk/confidence
  - SHAP `TreeExplainer` for top impact factors (fallback logic if SHAP unavailable)
- `features.py`: feature engineering contract
- `seed_data.py`: synthetic data generation for training bootstrap

Prediction behavior includes incomplete-data handling via training means + confidence adjustment.

---

## 5) Operational AI Layer (Governed Conversational Actions)

Core implementation: `app/services/conversational_ops_service.py` + `api/routes/operational_ai.py`

### Pipeline
1. Parse user message into structured intent (LLM JSON extraction with keyword fallback)
2. Normalize entity + filters + values
3. Enforce permission matrix and department scope restrictions
4. Estimate impact and classify risk (LOW/MEDIUM/HIGH)
5. Execute operation directly (no approval gates, no confirmation prompts)
6. Persist immutable audit trail and support rollback path

### Governance notes
- Role matrix by operation (`READ/CREATE/UPDATE/DELETE/ANALYZE`)
- Risk thresholds configurable via settings
- All operations execute immediately — no pending queue or 2FA
- API endpoints: single `/execute` entry point, rollback, audit history, and aggregate stats

---

## 6) Frontend Architecture

## 6.1 Bootstrapping and Routing
- Entry: `frontend/src/App.jsx`
- React Router with role-based guarded routes (`student`, `faculty`, `admin`).
- `ProtectedRoute` checks auth state and role authorization.

Primary pages include:
- `Login`, `StudentDashboard`, `StudentProfile`, `AttendanceDetails`
- `FacultyConsole`
- `AdminPanel`, `UserManagement`, `CourseManagement`, `DepartmentManagement`
- `CopilotPanel`, `GovernanceDashboard`
- `FinanceManagement`, `HRManagement`, `Timetable`

## 6.2 State and API Integration
- `context/AuthContext.jsx`
  - Hydrates user from `/api/auth/me` using cookie session.
- `services/api.js`
  - Centralized `fetch` wrapper
  - Error normalization and automatic 401 redirect to login
  - Endpoint methods across all ERP modules
  - Single `operationalAIExecute(message, module)` method for ops AI
- `services/operationalAI.contract.js`
  - Frontend contract builders for `/api/ops-ai` payload consistency
  - Simplified: `buildConversationalPayload`, `buildOperationalRollbackPayload`, `buildAuditQuery`

## 6.3 Build/Dev Server
- `vite.config.js`
  - Dev server on `5173`
  - `/api` proxy to backend target (`VITE_API_PROXY_TARGET`, default `http://localhost:8000`)
  - Cookie domain rewrite for local session flow

---

## 7) Deployment & Runtime Topologies

## 7.1 Docker Compose (Development / Split Services)
Defined in `docker-compose.yml`:
- `db` (PostgreSQL 16)
- `redis` (Redis 7)
- `backend` (FastAPI on `8000`)
- `frontend` (Vite on `5173`)

Backend startup command seeds DB then launches Uvicorn.

## 7.2 Single-Server Production Mode
Documented in README + production compose files:
- FastAPI can serve built frontend static assets from `frontend/dist`.
- Operationally reduces separate frontend hosting dependency.

---

## 8) Testing and Quality Signals

Backend tests present in `backend/tests/`:
- `test_auth.py`
- `test_operational_ai.py`
- `test_risk_classification.py`
- `test_students.py`
- shared fixtures in `conftest.py`

Additional root-level PowerShell test helpers exist for deployment/console/Gemini checks.

---

## 9) Configuration Surface (Important Environment Variables)

From backend settings and docs:
- Core: `DEBUG`, `SECRET_KEY`, `DATABASE_URL`
- JWT: `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- Gemini: `GEMINI_API_KEY`, `GEMINI_MODEL` (default `gemini-2.0-flash`), `GEMINI_TEMPERATURE_JSON`, `GEMINI_TEMPERATURE_CHAT`, `GEMINI_MAX_OUTPUT_TOKENS`, `GEMINI_MAX_RETRIES`, `GEMINI_RETRY_DELAY`
- Ops AI controls: `OPS_CONFIDENCE_THRESHOLD`, `OPS_MAX_PREVIEW_ROWS`
- Risk thresholds: `RISK_HIGH_IMPACT_COUNT`, `RISK_MEDIUM_IMPACT_COUNT`
- Frontend: `SERVE_FRONTEND`, `FRONTEND_DIST_PATH`
- ML path: `MODEL_PATH`

---

## 10) Observed Strengths and Engineering Considerations

### Strengths
- Clear backend modularization (routes/services/models/schemas/core/ml)
- Good AI fault tolerance (Gemini retry with exponential backoff + keyword/rule fallback)
- Direct-execution operational AI with immutable audit trail and rollback semantics
- Role-based frontend routing aligned to backend authorization model

### Considerations
- In-memory password reset token store should be replaced with Redis/DB for production durability
- Multiple documentation files exist; risk of drift unless a canonical technical source is maintained
- Security-sensitive defaults (`DEBUG`, default secrets) must be hardened per environment

---

## 11) Suggested Canonical Reading Order for Engineers

1. `README.md` (system capabilities + run paths)
2. `backend/app/main.py` (runtime composition)
3. `backend/app/core/config.py` (config contract)
4. `backend/app/models/models.py` (domain + persistence)
5. `backend/app/services/conversational_ops_service.py` (highest complexity logic)
6. `frontend/src/App.jsx` + `frontend/src/services/api.js` (UI flow + API contract)
7. `backend/app/ml/train.py` + `backend/app/ml/predict.py` (prediction subsystem)

---

## 12) Quick Start Commands (Engineering)

### Local dev (split stack)
```bash
# from repo root
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cd ../frontend
npm install

# optional infra
cd ..
docker-compose up -d db redis
```

### Full dockerized
```bash
docker-compose up --build
```

### Backend tests
```bash
cd backend
pytest
```

---

If you want, this file can be extended next with a **module dependency graph** and **endpoint-to-service-to-model mapping matrix** for onboarding and audits.
