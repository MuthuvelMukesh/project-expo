# 🚀 Quick Start - CampusIQ Single Server

## ✅ Status: READY TO RUN!

Both frontend and backend are production-ready and combined into a single server.

---

## 📋 Prerequisites

### Required:
- **Google Gemini API Key** (FREE) - [Get it here](https://aistudio.google.com/app/apikey)
- **Docker** (recommended) OR **Python 3.11+** and **Node.js 18+**

### Optional:
- PostgreSQL 16 (or use Docker)
- Redis (or use Docker)

---

## 🔑 Step 1: Get Gemini API Key (Required)

CampusIQ uses Google's Gemini API for AI-powered features.

1. **Visit**: https://aistudio.google.com/app/apikey
2. **Sign in** with your Google account
3. **Click "Create API Key"**
4. **Copy the API key** (starts with `AIzaSy...`)

💡 **It's FREE!** 15 requests/min, 1,500/day — perfect for development.

---

## ⚙️ Step 2: Configure API Key

### Option A: Using .env File (Recommended)

```powershell
# 1. Open .env file in project root
notepad .env

# 2. Add your API key (replace with your actual key)
GOOGLE_API_KEY=AIzaSy_YOUR_API_KEY_HERE

# 3. Save and close
```

### Option B: Using Environment Variable

```powershell
# Temporary for current session
$env:GOOGLE_API_KEY = "AIzaSy_YOUR_API_KEY_HERE"
```

---

## 🧪 Step 3: Test API Connection (Optional)

Verify your API key is working:

```powershell
.\test_gemini_api.ps1
```

**Expected output**:
```
✅ SUCCESS! Gemini API is working!
Response from Gemini: "Hello from CampusIQ today!"
```

---

## 🏃 Step 4: Start the Application

### Windows (PowerShell):
```powershell
# 1. Make sure you have Docker installed and running
# 2. Run the production build
.\start_production.ps1

# OR use Docker Compose:
docker-compose -f docker-compose.production.yml up --build
```

### Linux/Mac:
```bash
# 1. Make scripts executable
chmod +x build_production.sh

# 2. Run production build
./build_production.sh

# 3. Start backend
cd backend
pip install -r requirements.txt
python -m app.seed_db
uvicorn app.main:app --host 0.0.0.0 --port 8000

# OR use Docker:
docker-compose -f docker-compose.production.yml up --build
```

---

## 🌐 Access Your Application

After starting:

- **Frontend UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 📝 Default Login Credentials

```
Email: admin@campusiq.edu
Password: admin123
```

---

## 🛠️ What's Running?

- **Port 8000**: Combined Frontend + Backend Server
- **Port 5433**: PostgreSQL Database (Docker)
- **Port 6379**: Redis Cache (Docker)

---

## 📖 Full Documentation

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.

---

**Happy Learning! 🎓**
