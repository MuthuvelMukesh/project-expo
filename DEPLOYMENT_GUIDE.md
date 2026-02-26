# 🚀 CampusIQ - Single Server Deployment Guide

## ✅ Status: Both Frontend and Backend are Ready!

Both the frontend and backend have been verified and are **production-ready**. They have now been combined into a **single server** for easier deployment.

---

## 📋 What Changed?

### Previous Setup (Development)
- **Frontend**: Separate Vite dev server on port 5173
- **Backend**: FastAPI server on port 8000
- **Deployment**: 3 separate Docker containers

### New Setup (Production)
- **Single Server**: FastAPI serves both API and frontend
- **Port**: Single port 8000 for everything
- **Deployment**: 1 Docker container (+ database + redis)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│  Single Server (Port 8000)         │
│  ┌───────────────────────────────┐ │
│  │   FastAPI Backend             │ │
│  │   - API Routes (/api/*)       │ │
│  │   - ML/AI Services            │ │
│  │   - Authentication            │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │   Frontend Static Files       │ │
│  │   - React SPA                 │ │
│  │   - Built with Vite           │ │
│  │   - Served from /             │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
         ↓              ↓
    PostgreSQL       Redis
    (Port 5433)   (Port 6379)
```

---

## 🚀 Quick Start (Windows PowerShell)

### Option 1: Build and Run (Recommended)

```powershell
# Build frontend and start production server
.\start_production.ps1
```

This script will:
1. ✓ Build the frontend if not already built
2. ✓ Create and activate Python virtual environment
3. ✓ Install backend dependencies
4. ✓ Seed the database
5. ✓ Start the combined server on port 8000

### Option 2: Docker Compose (Production)

```powershell
# Build and start all services
docker-compose -f docker-compose.production.yml up --build

# Or run in detached mode
docker-compose -f docker-compose.production.yml up -d
```

### Option 3: Manual Build and Run

```powershell
# Step 1: Build frontend
cd frontend
npm install
npm run build
cd ..

# Step 2: Install backend dependencies
cd backend
pip install -r requirements.txt

# Step 3: Seed database (if needed)
python -m app.seed_db

# Step 4: Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 🌐 Access Points

After starting the server:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend UI** | http://localhost:8000 | Main application interface |
| **API Documentation** | http://localhost:8000/docs | Interactive API docs (Swagger) |
| **ReDoc** | http://localhost:8000/redoc | Alternative API documentation |
| **Health Check** | http://localhost:8000/health | Server health status |
| **Database** | localhost:5433 | PostgreSQL (docker) |
| **Redis** | localhost:6379 | Redis cache |

---

## 📦 Prerequisites

### For Local Development/Production:
- **Python 3.11+**
- **Node.js 18+** and npm
- **PostgreSQL 16** (or use Docker)
- **Redis** (or use Docker)

### For Docker Deployment:
- **Docker** and **Docker Compose**

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database
DB_PASSWORD=your_secure_password

# Security
SECRET_KEY=your_secret_key_here

# Google Gemini API
GOOGLE_API_KEY=your_gemini_api_key
GOOGLE_MODEL=gemini-1.5-flash

# Optional: Module-specific API keys
GEMINI_NLP_KEYS=key1,key2,key3
GEMINI_PREDICTIONS_KEYS=key1,key2
GEMINI_FINANCE_KEYS=key1,key2
GEMINI_HR_KEYS=key1,key2
GEMINI_CHAT_KEYS=key1,key2
```

---

## 🧪 Testing the Deployment

### 1. Check Health
```powershell
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

### 2. Access Frontend
Open browser: http://localhost:8000

### 3. Test API
Open: http://localhost:8000/docs

Try the authentication endpoint:
```json
POST /api/auth/login
{
  "email": "admin@campusiq.edu",
  "password": "admin123"
}
```

---

## 🐳 Docker Commands

### Start Services
```bash
docker-compose -f docker-compose.production.yml up -d
```

### View Logs
```bash
docker-compose -f docker-compose.production.yml logs -f app
```

### Stop Services
```bash
docker-compose -f docker-compose.production.yml down
```

### Rebuild and Restart
```bash
docker-compose -f docker-compose.production.yml up --build -d
```

### Clean Everything
```bash
docker-compose -f docker-compose.production.yml down -v
```

---

## 📁 Project Structure

```
project-expo/
├── backend/
│   ├── app/
│   │   ├── main.py              # ✨ Now serves frontend too!
│   │   ├── api/                 # API routes
│   │   ├── models/              # Database models
│   │   ├── services/            # Business logic
│   │   └── ml/                  # ML models
│   └── requirements.txt         # ✨ Updated with aiofiles
├── frontend/
│   ├── src/                     # React source
│   ├── dist/                    # ✨ Built files (served by backend)
│   └── package.json
├── docker-compose.production.yml # ✨ Single server compose file
├── Dockerfile.production        # ✨ Multi-stage build
├── build_production.ps1        # ✨ Build script (Windows)
├── build_production.sh         # ✨ Build script (Linux/Mac)
└── start_production.ps1        # ✨ Startup script
```

---

## 🔄 Development vs Production

### Development Mode (Separate Servers)
```bash
# Use original docker-compose.yml
docker-compose up
```
- Frontend: http://localhost:5173 (hot reload)
- Backend: http://localhost:8000

### Production Mode (Single Server)
```bash
# Use new production compose file
docker-compose -f docker-compose.production.yml up
```
- Everything: http://localhost:8000

---

## 🎯 Key Features

✅ **Single Port Deployment** - Everything on port 8000  
✅ **SPA Routing Support** - Proper React Router handling  
✅ **Static Asset Optimization** - Efficient file serving  
✅ **API and Frontend Separation** - Clean URL structure  
✅ **Production Build** - Optimized and minified frontend  
✅ **Docker Ready** - Multi-stage build for efficiency  
✅ **Health Checks** - Built-in monitoring  
✅ **Auto Restart** - Container restart policies  

---

## 🚨 Troubleshooting

### Frontend not loading
```powershell
# Rebuild frontend
cd frontend
npm run build
```

### Database connection errors
```powershell
# Check if database is running
docker-compose -f docker-compose.production.yml ps
```

### Port already in use
```powershell
# Change port in startup script
.\start_production.ps1 -Port 8080
```

### Static files not found
Ensure the build exists:
```powershell
Test-Path .\frontend\dist\index.html
```

---

## 📊 Performance Tips

1. **Enable Gzip Compression** - Add middleware for compression
2. **Cache Static Assets** - Configure browser caching
3. **Use CDN** - For production deployments
4. **Database Connection Pooling** - Already configured
5. **Redis Caching** - Implemented for session management

---

## 🔐 Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Use strong DB_PASSWORD
- [ ] Enable HTTPS (reverse proxy)
- [ ] Configure CORS properly
- [ ] Set up firewall rules
- [ ] Regular security updates
- [ ] Monitor logs
- [ ] Implement rate limiting

---

## 📝 Next Steps

1. **Configure Environment Variables** - Set up `.env` file
2. **Test the Application** - Run through all features
3. **Set up HTTPS** - Use nginx or Caddy as reverse proxy
4. **Configure Domain** - Point DNS to your server
5. **Set up Monitoring** - Add logging and alerting
6. **Backup Strategy** - Regular database backups

---

## 🆘 Need Help?

- Check logs: `docker-compose -f docker-compose.production.yml logs -f`
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

---

**🎉 Congratulations! Your CampusIQ application is now running on a single server!**
