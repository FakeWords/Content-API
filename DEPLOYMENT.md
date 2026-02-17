# 🚀 Deployment Guide - Get Your API Online and Monetized

This guide walks you through deploying your Content Moderation API and listing it on marketplaces to start earning money.

## 🎯 Overview: Path to Revenue

1. **Deploy** your API to the cloud (15 minutes)
2. **Test** it's working publicly (5 minutes)
3. **List** on API marketplace (30 minutes)
4. **Market** to first customers (ongoing)

Estimated time to first deployment: **1 hour**

---

## Option 1: Railway (Recommended - Easiest)

Railway is the simplest way to deploy. It automatically detects your Python app and deploys it.

### Cost
- **Hobby Plan**: $5/month for 500 hours
- **Pro Plan**: $20/month for unlimited

### Steps

1. **Create a Railway account**
   - Go to: https://railway.app
   - Sign up with GitHub (recommended)

2. **Install Railway CLI** (optional, but helpful)
   ```bash
   npm install -g railway
   # or
   curl -fsSL https://railway.app/install.sh | sh
   ```

3. **Prepare your code**
   
   Add a `Procfile` to tell Railway how to run your app:
   ```bash
   echo "web: uvicorn content_moderation_api:app --host 0.0.0.0 --port \$PORT" > Procfile
   ```
   
   Add a `runtime.txt` to specify Python version:
   ```bash
   echo "python-3.11.0" > runtime.txt
   ```

4. **Deploy via Web UI** (easiest)
   
   - Go to Railway dashboard
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository (or upload code)
   - Railway auto-detects Python and installs dependencies
   - Click "Generate Domain" to get a public URL
   
   **OR Deploy via CLI:**
   ```bash
   railway login
   railway init
   railway up
   railway open
   ```

5. **Get your API URL**
   - In Railway dashboard, click "Generate Domain"
   - Your API is now live at: `https://your-app.railway.app`
   - Test it: `https://your-app.railway.app/docs`

### Monitoring
Railway provides:
- Real-time logs
- CPU/Memory usage
- Request metrics
- Automatic SSL certificates

---

## Option 2: Heroku (Popular, Well-Documented)

### Cost
- **Eco Dyno**: $7/month (good for MVP)
- **Basic**: $7/month per dyno
- **Standard**: $25-50/month

### Steps

1. **Install Heroku CLI**
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku
   
   # Windows
   # Download from: https://devcenter.heroku.com/articles/heroku-cli
   
   # Linux
   curl https://cli-assets.heroku.com/install.sh | sh
   ```

2. **Login and create app**
   ```bash
   heroku login
   heroku create your-moderation-api
   ```

3. **Add required files**
   
   Create `Procfile`:
   ```
   web: uvicorn content_moderation_api:app --host=0.0.0.0 --port=${PORT}
   ```
   
   Update `requirements.txt` if needed (already done!)

4. **Initialize git and deploy**
   ```bash
   git init
   git add .
   git commit -m "Initial deployment"
   git push heroku main
   ```

5. **Open your API**
   ```bash
   heroku open
   # or visit: https://your-moderation-api.herokuapp.com
   ```

6. **View logs**
   ```bash
   heroku logs --tail
   ```

---

## Option 3: AWS Lambda + API Gateway (Serverless)

**Best for:** Pay-per-request pricing, automatic scaling

**Complexity:** ⭐⭐⭐⭐ (More advanced)

### Cost
- **Free tier**: 1M requests/month free
- **After**: $0.20 per 1M requests

### Quick Setup with Zappa

1. **Install Zappa**
   ```bash
   pip install zappa
   ```

2. **Initialize**
   ```bash
   zappa init
   ```

3. **Deploy**
   ```bash
   zappa deploy production
   ```

4. **Update**
   ```bash
   zappa update production
   ```

---

## Option 4: DigitalOcean App Platform

### Cost
- **Basic**: $5/month
- **Pro**: $12/month

### Steps
1. Go to: https://cloud.digitalocean.com/apps
2. Click "Create App"
3. Connect GitHub repo
4. Configure:
   - **Type**: Web Service
   - **Build Command**: `pip install -r requirements.txt`
   - **Run Command**: `uvicorn content_moderation_api:app --host 0.0.0.0 --port 8080`
5. Click "Create Resources"

---

## 🧪 Testing Your Deployed API

Once deployed, test it works:

### Test with cURL
```bash
curl -X POST "https://your-api-url.com/moderate" \
  -H "Content-Type: application/json" \
  -d '{"text": "Test message", "sensitivity": "medium"}'
```

### Test with Python
```python
import requests

response = requests.post(
    "https://your-api-url.com/moderate",
    json={"text": "This is a test", "sensitivity": "medium"}
)
print(response.json())
```

### Load Testing
Use this free tool to test performance:
```bash
# Install hey (load testing tool)
# macOS: brew install hey
# Linux: go install github.com/rakyll/hey@latest

# Test your API
hey -n 100 -c 10 -m POST \
  -H "Content-Type: application/json" \
  -d '{"text":"test","sensitivity":"medium"}' \
  https://your-api-url.com/moderate
```

---

## 💰 Listing on API Marketplaces

### Option A: RapidAPI (Most Traffic)

**Pros:**
- Largest API marketplace
- 4M+ developers
- Built-in billing

**Cons:**
- 20% commission on sales

**Steps:**

1. **Create Account**
   - Go to: https://rapidapi.com/provider
   - Click "Become a Provider"

2. **Add Your API**
   - Dashboard → "My APIs" → "Add New API"
   - Fill in details:
     - **Name**: Content Moderation API
     - **Category**: Text Analysis / AI
     - **Base URL**: https://your-api-url.com
   
3. **Configure Endpoints**
   - Add `/moderate` endpoint
   - Define request/response schemas
   - Add example requests

4. **Set Pricing**
   
   **Recommended Tiers:**
   
   **Free Tier** (for testing)
   - 500 requests/month
   - All features
   - Attracts users to try
   
   **Basic** - $19/month
   - 10,000 requests
   - Standard support
   
   **Pro** - $49/month
   - 50,000 requests
   - Priority support
   
   **Ultra** - $99/month
   - 200,000 requests
   - Batch processing
   - Custom categories

5. **Submit for Review**
   - Usually approved within 24-48 hours
   - Test thoroughly before submitting

### Option B: DigitalAPI Marketplace

**Pros:**
- Lower fees
- Modern platform
- Good for AI APIs

**Steps:**

1. Go to: https://digitalapi.com
2. Click "Publish API"
3. Follow guided setup
4. Similar to RapidAPI process

### Option C: APILayer

**Pros:**
- Developer-focused audience
- Good documentation tools

**Steps:**
1. Visit: https://apilayer.com
2. "Submit Your API"
3. Provide API documentation
4. Set pricing tiers

---

## 🔐 Adding Authentication & Rate Limiting

Before going to production, add security:

### Simple API Key Auth

```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != "your-secret-key":  # Use env variable in production
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

@app.post("/moderate")
async def moderate_content(
    request: ModerationRequest,
    api_key: str = Depends(verify_api_key)
):
    # ... existing code
```

### Rate Limiting

```bash
pip install slowapi
```

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/moderate")
@limiter.limit("100/minute")  # 100 requests per minute
async def moderate_content(request: Request, ...):
    # ... existing code
```

---

## 📊 Monitoring & Analytics

### Free Tools

**1. Better Stack (Uptime Monitoring)**
- https://betterstack.com
- Free tier: 10 monitors
- Get alerts if API goes down

**2. Grafana Cloud (Free tier)**
- https://grafana.com
- Track API metrics
- Free up to 10k series

**3. Sentry (Error Tracking)**
```bash
pip install sentry-sdk
```

```python
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0,
)
```

---

## 📈 Marketing Your API

### 1. Create Landing Page
Use these free tools:
- **Carrd**: Simple one-page sites ($19/year)
- **Vercel**: Free hosting for static sites
- **GitHub Pages**: Free

Include:
- What problem you solve
- Pricing
- Code examples
- "Try it free" button

### 2. Developer Communities

Post on:
- **Reddit**: r/webdev, r/javascript, r/python
- **Dev.to**: Write tutorial using your API
- **Hacker News**: Show HN post
- **Product Hunt**: Launch there

### 3. Content Marketing

Create tutorials:
- "How to moderate chat in real-time"
- "Building a safe community platform"
- "Content moderation for indie developers"

Post on:
- Medium
- Dev.to  
- Your own blog

### 4. Direct Outreach

Find potential customers:
- Discord server owners
- Forum administrators
- Indie game developers
- Social app builders

---

## 💡 First 10 Customers Strategy

**Week 1-2: Launch**
1. Deploy API ✅
2. List on RapidAPI ✅
3. Create landing page ✅
4. Post on Reddit/HN ✅

**Week 3-4: Outreach**
1. Email 50 potential customers
2. Offer 3 months free for feedback
3. Join Discord communities for developers
4. Offer integration help

**Month 2: Iterate**
1. Add most-requested features
2. Improve documentation
3. Create video tutorials
4. Case study with early customer

**Month 3: Scale**
1. Paid ads on RapidAPI marketplace
2. Write guest posts
3. Sponsor developer newsletters
4. Launch affiliate program

---

## 🎯 Success Metrics

Track these to measure growth:

**Week 1:**
- [ ] API deployed and stable
- [ ] Listed on 1 marketplace
- [ ] First test user

**Month 1:**
- [ ] 10 free tier users
- [ ] 2 paying customers
- [ ] $50 MRR (Monthly Recurring Revenue)

**Month 3:**
- [ ] 50+ users
- [ ] 10 paying customers
- [ ] $300+ MRR

**Month 6:**
- [ ] 200+ users
- [ ] 30+ paying customers
- [ ] $1000+ MRR

---

## 🆘 Troubleshooting

### API won't start
```bash
# Check logs
railway logs  # Railway
heroku logs --tail  # Heroku

# Common issues:
# - Port binding: Use $PORT environment variable
# - Dependencies: Check requirements.txt
# - Python version: Specify in runtime.txt
```

### Slow response times
```python
# Add caching
from functools import lru_cache

@lru_cache(maxsize=1000)
def moderate_cached(text_hash):
    # ... moderation logic
```

### High costs
- Implement aggressive rate limiting
- Add API key authentication
- Use cheaper hosting for free tier users
- Upgrade to reserved instances

---

## 📚 Next Steps

1. **Deploy** (pick one platform, start today)
2. **Test** thoroughly
3. **List** on marketplace
4. **Get feedback** from first users
5. **Iterate** based on real usage

**Remember:** Perfect is the enemy of done. Ship the MVP, learn from real users, improve iteratively.

---

## 🤝 Need Help?

- Railway Discord: https://discord.gg/railway
- Heroku Support: https://help.heroku.com
- RapidAPI Docs: https://docs.rapidapi.com
- FastAPI Discord: https://discord.com/invite/fastapi

**Good luck! 🚀**
