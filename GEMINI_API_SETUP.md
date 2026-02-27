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

For production deployments with higher traffic, consider upgrading to a paid tier.

---

## Step 2: Configure CampusIQ

### Option A: Using `.env` File (Recommended)

1. **Navigate to the project root** directory:
   ```bash
   cd /path/to/project-expo
   ```

2. **Open or create `.env` file**:
   ```bash
   nano .env
   ```

3. **Add your API key**:
   ```env
   # Required: Gemini API Key
   GEMINI_API_KEY=AIzaSy_YOUR_API_KEY_HERE
   GEMINI_MODEL=gemini-2.0-flash
   ```

4. **Save and close** the file

### Option B: Using Docker Environment Variables

If using Docker Compose, update `docker-compose.yml` or `docker-compose.production.yml`:

```yaml
environment:
  GEMINI_API_KEY: "AIzaSy_YOUR_API_KEY_HERE"
  GEMINI_MODEL: "gemini-2.0-flash"
```

### Option C: Using Shell Environment (Temporary Session)

For quick testing:
```bash
export GEMINI_API_KEY="AIzaSy_YOUR_API_KEY_HERE"
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
✅ Good: "Gemini response received"
❌ Bad: "GEMINI_API_KEY not set"
❌ Bad: "Gemini API error: RATE_LIMITED"
```

---

## Troubleshooting

### Error: "No Gemini keys configured"

**Cause**: API key not set in environment

**Fix**:
```env
# Add to .env
GEMINI_API_KEY=AIzaSy_YOUR_KEY_HERE
```

### Error: "RATE_LIMITED"

**Cause**: Exceeded free tier limits (15 req/min)

**Solutions**:
1. **Wait 60 seconds** for quota reset
2. **Reduce request frequency**
3. **Upgrade to paid tier** if available

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

CampusIQ is configured to use **Gemini 2.0 Flash** by default (fast and efficient).

### Available Models

| Model | Speed | Intelligence | Best For |
|-------|-------|--------------|----------|
| `gemini-2.0-flash` | ⚡⚡⚡ Fast | ⭐⭐⭐ Excellent | **Default** - General use |
| `gemini-2.5-flash` | ⚡⚡⚡ Fast | ⭐⭐⭐ Excellent | Latest thinking model |

### Change Model (if needed)

In `.env`:
```env
GEMINI_MODEL=gemini-2.5-flash
```

---

## Performance Optimizations Applied

✅ **Single Client Instance**: Reuses a single `GeminiClient` for all requests  
✅ **Automatic Retry Logic**: Retries on transient failures  
✅ **Graceful Degradation**: Falls back to rule-based responses if API unavailable  
✅ **Temperature Tuning**: Low (0.1) for JSON parsing, moderate (0.4) for chat  
✅ **Model Configuration**: Configurable via `GEMINI_MODEL` env var  

---

## Security Best Practices

### ⚠️ **Never commit API keys to Git**

The `.env` file is in `.gitignore` by default.

### ✅ **Use environment variables in production**

For Docker, Kubernetes, or cloud deployments:
```bash
docker run -e GEMINI_API_KEY=your_key campusiq
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

```bash
# Check if API key is set
echo $GEMINI_API_KEY

# Test the application with your key
./start_production.sh

# View logs for API issues
cd backend
uvicorn app.main:app --reload

# Test chatbot endpoint
curl http://localhost:8000/api/chatbot/query -X POST -H "Content-Type: application/json" -d '{"message": "Hello"}'
```

---

**✅ Setup Complete!** Your CampusIQ application is now connected to Google Gemini AI.
