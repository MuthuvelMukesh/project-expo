# ═══════════════════════════════════════════════════════════════
# CampusIQ — Local Development Setup (Complete)
# ═══════════════════════════════════════════════════════════════

## ✅ What's Running

### Services (Docker):
- **PostgreSQL 16**: Running on port 5433 (healthy)
- **Redis 7**: Running on port 6379 (healthy)

### Backend (Local):
- **FastAPI**: Running on http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health ✓ (200 OK)

## 📋 Setup Summary

### 1. Docker Services (PostgreSQL + Redis)
```bash
docker-compose up -d
```
- Uses simplified `docker-compose.yml` (services only, no app containers)
- PostgreSQL: `campusiq-db` on port 5433
- Redis: `campusiq-redis` on port 6379

### 2. Python Dependencies
All required packages installed:
- fastapi, uvicorn, pydantic, sqlalchemy
- scikit-learn, xgboost, pandas, numpy
- google-generativeai, httpx
- pytest, alembic, asyncpg

**Note**: Used flexible version constraints (`>=`) to avoid compilation issues

### 3. Backend Server
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server is running in background terminal (ID: 14e461cd-12fb-4fe3-9bd9-a8b028b46f7b)

## 🚀 Start Frontend

### Option 1: Development Server (Recommended)
```bash
cd frontend
npm install
npm run dev
```
Frontend will run at **http://localhost:5173**

### Option 2: Production Build (Served by Backend)
```bash
cd frontend
npm install
npm run build
```
Then access at **http://localhost:8000** (backend serves static files)

## 🔧 Configuration

### Environment Variables (.env)
```
DATABASE_URL=postgresql+asyncpg://campusiq:campusiq_secret@127.0.0.1:5433/campusiq
GEMINI_API_KEY=AIzaSyBc_1isBU9KIM3CXcj1MLiu84jZuuKmb2w
GEMINI_MODEL=gemini-2.0-flash
```

### Database Connection
- **Issue**: asyncpg SSL connection issues on Windows
- **Solution**: Modified `backend/app/core/database.py` with:
  ```python
  connect_args={"ssl": False, "server_settings": {}}
  ```
- **Note**: Database seeding skipped due to SQLAlchemy/asyncpg SSL configuration conflict
  - Tables will be created automatically on first API request
  - Seed data can be added manually or through API calls

## 📝 Quick Commands

### Start Everything
```powershell
# Terminal 1: Start Docker services
docker-compose up -d

# Terminal 2: Start backend
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3: Start frontend
cd frontend
npm run dev
```

### Stop Everything
```powershell
# Stop backend: Ctrl+C in terminal
# Stop frontend: Ctrl+C in terminal
# Stop Docker services:
docker-compose down
```

### Check Status
```powershell
# Docker services
docker ps

# Backend health
curl http://localhost:8000/health

# View backend logs
# (Check terminal where uvicorn is running)
```

## 🎯 Next Steps

1. **Start Frontend Development Server**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

2. **Access Application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

3. **Create Demo Data** (if needed)
   - Use API endpoints to create users, students, courses
   - Or run `python -m app.seed` after fixing SSL configuration

## 🐛 Troubleshooting

### Backend won't connect to database
- Check Docker containers are running: `docker ps`
- Verify port 5433 is not used by another service
- Restart PostgreSQL: `docker restart campusiq-db`

### Frontend build errors
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Clear npm cache: `npm cache clean --force`

### Python package installation issues
- Some packages (scikit-learn, xgboost) have newer versions pre-installed
- requirements.txt updated to use flexible versions (`>=`)
- If issues persist, install Visual C++ Build Tools

## 📦 File Changes Made

1. **docker-compose.yml**: Simplified to services only (PostgreSQL + Redis)
2. **backend/requirements.txt**: Updated with flexible versions
3. **backend/app/core/database.py**: Added SSL=False for local dev
4. **.env**: Changed localhost→127.0.0.1, added SSL disable parameter
5. **start_local_dev.ps1**: Created centralized startup script

## ✨ Benefits of This Setup

- **Faster Development**: No container rebuilds for code changes
- **Better Debugging**: Direct access to Python debugger
- **Easier Testing**: Run pytest directly
- **Simpler Dependencies**: Uses system Python (no Docker layer)
- **Mixed Approach**: Docker for services, local for apps

---

**Status**: Backend running successfully ✅  
**Next**: Start frontend development server
