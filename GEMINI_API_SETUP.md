# 🔑 Google Gemini API Setup Guide

## Quick Start

CampusIQ uses Google's Gemini API for all AI-powered features. Follow these steps to get your API key and configure the application.

---

## Step 1: Get Your FREE Gemini API Key

1. **Visit Google AI Studio**: https://aistudio.google.com/app/apikey
2. **Sign in** with your Google account
3. **Click "Create API Key"**
4. **Copy the API key** (starts with `AIzaSy...`)

### API Key Limits (Free Tier)
- ✅ **15 requests per minute**
- ✅ **1,500 requests per day**
- ✅ **1 million tokens per minute**
- ✅ **Unlimited** for development use

For production deployments with higher traffic, consider:
- Using multiple API keys (key pooling)
- Upgrading to paid tier (if available)

---

## Step 2: Configure CampusIQ

### Option A: Using `.env` File (Recommended)

1. **Navigate to the project root** directory:
   ```bash
   cd d:\project expo\project-expo
   ```

2. **Open or create `.env` file**:
   ```bash
   notepad .env
   ```

3. **Add your API key**:
   ```env
   # Required: Main Gemini API Key
   GOOGLE_API_KEY=AIzaSy_YOUR_API_KEY_HERE
   GOOGLE_BASE_URL=https://generativelanguage.googleapis.com/v1beta
   GOOGLE_MODEL=gemini-1.5-flash
   
   # Optional: Module-specific key pools (for high-traffic production)
   GEMINI_NLP_KEYS=
   GEMINI_PREDICTIONS_KEYS=
   GEMINI_FINANCE_KEYS=
   GEMINI_HR_KEYS=
   GEMINI_CHAT_KEYS=
   ```

4. **Save and close** the file

### Option B: Using Docker Environment Variables

If using Docker Compose, update `docker-compose.yml` or `docker-compose.production.yml`:

```yaml
environment:
  GOOGLE_API_KEY: "AIzaSy_YOUR_API_KEY_HERE"
  GOOGLE_MODEL: "gemini-1.5-flash"
```

### Option C: Using PowerShell (Temporary Session)

For quick testing:
```powershell
$env:GOOGLE_API_KEY = "AIzaSy_YOUR_API_KEY_HERE"
cd backend
uvicorn app.main:app --reload
```

---

## Step 3: Verify Configuration

### Test the API Connection

1. **Start the server**:
   ```powershell
   .\start_production.ps1
   ```

2. **Open API documentation**:
   ```
   http://localhost:8000/docs
   ```

3. **Test the chatbot endpoint**:
   - Navigate to `/api/chatbot/query`
   - Click "Try it out"
   - Enter a test message: "What is CampusIQ?"
   - Click "Execute"

4. **Expected response**:
   ```json
   {
     "response": "CampusIQ is an AI-powered college ERP system...",
     "sources": ["CampusIQ AI (Gemini)"],
     "suggested_actions": [...]
   }
   ```

### Check Logs for API Issues

If you see errors, check the console logs:
```
✅ Good: "Gemini chat pool response received"
❌ Bad: "No Gemini keys configured for module 'chat'"
❌ Bad: "Gemini chat pool error: RATE_LIMITED"
```

---

## Advanced Configuration: Key Pooling

For **production deployments** with high traffic, use module-specific key pools to distribute API calls across multiple keys.

### Why Use Key Pools?

- **Better rate limit management**: Each key has its own quota
- **Automatic failover**: If one key is rate-limited, others are tried
- **Module isolation**: Different features use different keys

### How to Set Up Key Pools

1. **Get multiple API keys** from Google AI Studio

2. **Configure in `.env`**:
   ```env
   # Main fallback key
   GOOGLE_API_KEY=AIzaSy_KEY_1_HERE
   
   # Module-specific pools (comma-separated)
   GEMINI_NLP_KEYS=AIzaSy_KEY_2,AIzaSy_KEY_3,AIzaSy_KEY_4
   GEMINI_PREDICTIONS_KEYS=AIzaSy_KEY_5,AIzaSy_KEY_6
   GEMINI_FINANCE_KEYS=AIzaSy_KEY_7
   GEMINI_HR_KEYS=AIzaSy_KEY_8
   GEMINI_CHAT_KEYS=AIzaSy_KEY_9,AIzaSy_KEY_10
   ```

3. **Each module will rotate through its pool** when making API calls

### Module Usage Guide

| Module | Features | Recommended Keys |
|--------|----------|------------------|
| **NLP** | Command Console, NLP CRUD | 2-3 keys |
| **Chat** | Chatbot, AI Assistant | 2-3 keys |
| **Predictions** | Grade predictions, ML insights | 1-2 keys |
| **Finance** | Finance AI features | 1 key |
| **HR** | HR & Payroll AI features | 1 key |

---

## Troubleshooting

### Error: "No Gemini keys configured"

**Cause**: API key not set in environment

**Fix**:
```env
# Add to .env
GOOGLE_API_KEY=AIzaSy_YOUR_KEY_HERE
```

### Error: "RATE_LIMITED"

**Cause**: Exceeded free tier limits (15 req/min)

**Solutions**:
1. **Wait 60 seconds** for quota reset
2. **Add more API keys** to the key pool
3. **Reduce request frequency**
4. **Increase GEMINI_RETRY_ETA_SECONDS** in .env:
   ```env
   GEMINI_RETRY_ETA_SECONDS=120
   ```

### Error: "Invalid API key"

**Cause**: Key is incorrect or expired

**Fix**:
1. **Verify key** at https://aistudio.google.com/app/apikey
2. **Regenerate key** if needed
3. **Update `.env` file** with new key

### Error: "SERVICE_UNAVAILABLE"

**Cause**: Gemini API is temporarily down or network issue

**Solutions**:
1. **Check internet connection**
2. **Verify Gemini API status**: https://status.cloud.google.com/
3. **Try again in a few minutes**
4. **Application will use rule-based fallback** automatically

### Error: "Connection timeout"

**Cause**: Network latency or firewall blocking

**Fix**:
1. **Check firewall settings**
2. **Verify proxy configuration** (if applicable)
3. **Increase timeout** (already optimized to 30s)

---

## API Models Available

CampusIQ is configured to use **Gemini 1.5 Flash** by default (fast and efficient).

### Available Models

| Model | Speed | Intelligence | Best For |
|-------|-------|--------------|----------|
| `gemini-1.5-flash` | ⚡⚡⚡ Fast | ⭐⭐ Good | **Default** - General use |
| `gemini-1.5-pro` | ⚡⚡ Moderate | ⭐⭐⭐ Excellent | Complex reasoning |
| `gemini-1.0-pro` | ⚡⚡ Moderate | ⭐⭐ Good | Legacy support |

### Change Model (if needed)

In `.env`:
```env
GOOGLE_MODEL=gemini-1.5-pro
```

---

## Performance Optimizations Applied

✅ **HTTP/2 Connection Pooling**: Reuses connections for faster API calls  
✅ **Key Pool Rotation**: Distributes load across multiple keys  
✅ **Automatic Retry Logic**: Retries with different keys on failure  
✅ **Graceful Degradation**: Falls back to rule-based responses if API unavailable  
✅ **Request Timeouts**: Optimized to 25s for JSON, 30s for text  
✅ **Connection Limits**: Max 100 connections, 20 keepalive  

---

## Security Best Practices

### ⚠️ **Never commit API keys to Git**

The `.env` file is in `.gitignore` by default.

### ✅ **Use environment variables in production**

For Docker, Kubernetes, or cloud deployments:
```bash
docker run -e GOOGLE_API_KEY=your_key campusiq
```

### ✅ **Rotate keys periodically**

Generate new keys every few months for security.

### ✅ **Monitor usage**

Check API usage at: https://aistudio.google.com/app/apikey

---

## Testing Without API Key

The application includes **rule-based fallbacks** for all AI features:

- ✅ Chatbot will use knowledge base responses
- ✅ NLP CRUD will use keyword-based detection
- ✅ Command Console will use regex-based parsing

**However**, for best experience, use a Gemini API key.

---

## Cost Information

### Free Tier (Current)
- **Cost**: $0
- **Limits**: 15 requests/min, 1,500/day
- **Perfect for**: Development, testing, small deployments

### Paid Tier (If Available)
- **Check pricing**: https://ai.google.dev/pricing
- **Benefits**: Higher rate limits, production SLA

---

## Need Help?

### Resources
- **Google AI Studio**: https://aistudio.google.com/
- **Gemini API Docs**: https://ai.google.dev/docs
- **CampusIQ Docs**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

### Support
- Check application logs for detailed error messages
- Test API key at https://aistudio.google.com/app/apikey
- Verify `.env` configuration

---

## Quick Reference Commands

```powershell
# Check if API key is set
$env:GOOGLE_API_KEY

# Test the application with your key
.\start_production.ps1

# View logs for API issues
cd backend
uvicorn app.main:app --reload

# Test chatbot endpoint
curl http://localhost:8000/api/chatbot/query -X POST -H "Content-Type: application/json" -d '{"message": "Hello"}'
```

---

**✅ Setup Complete!** Your CampusIQ application is now connected to Google Gemini AI.
