# 🌐 Cloud Deployment Guide - Centralized API Key

This guide shows how to deploy Shusrusha to the cloud so others can use it while you control the OpenAI API key and usage.

## 🎯 Benefits of Centralized Deployment

✅ **You control API costs** - All usage goes through your OpenAI account  
✅ **Easy user access** - Users just visit a URL, no setup required  
✅ **Usage monitoring** - Track who uses what through OpenAI dashboard  
✅ **Security** - API key stays on your server, not shared with users  
✅ **Updates** - Update once, everyone gets the latest version  

## 🚀 Deployment Options

### Option 1: Streamlit Cloud (Free & Easy)

**Steps:**
1. **Push to GitHub** (if not already done)
2. **Visit** https://streamlit.io/cloud
3. **Connect your GitHub** account
4. **Deploy** your repository
5. **Add API key** in Streamlit Cloud secrets

**Detailed Setup:**

#### 1. Prepare Repository
```bash
# Make sure your code is on GitHub
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

#### 2. Create Streamlit Cloud App
1. Go to https://share.streamlit.io/
2. Click "New app"
3. Choose your GitHub repository: `arijitmukherji/shusrusha`
4. Set main file path: `app.py`
5. Click "Deploy!"

#### 3. Add Secrets (API Key)
1. In your deployed app, click the hamburger menu (≡)
2. Choose "Settings" → "Secrets"
3. Add your API key:
```toml
OPENAI_API_KEY = "your_openai_api_key_here"
```

#### 4. Share the URL
Your app will be available at: `https://your-app-name.streamlit.app/`

**Cost**: FREE (with some limitations)

---

### Option 2: Railway (Simple & Reliable)

**Steps:**
1. **Sign up** at https://railway.app/
2. **Connect GitHub** and deploy repository
3. **Add environment variables**
4. **Get public URL**

**Detailed Setup:**

#### 1. Deploy to Railway
1. Visit https://railway.app/
2. Click "Start a New Project"
3. Choose "Deploy from GitHub repo"
4. Select your `shusrusha` repository
5. Railway auto-detects it's a Python app

#### 2. Configure Environment
1. Go to your project dashboard
2. Click "Variables" tab
3. Add: `OPENAI_API_KEY = your_key_here`
4. Add: `PORT = 8501`

#### 3. Custom Domain (Optional)
1. Go to "Settings" → "Domains"
2. Add custom domain or use Railway subdomain

**Cost**: $5/month after free tier

---

### Option 3: Render (Professional)

**Steps:**
1. **Connect GitHub** at https://render.com/
2. **Create Web Service**
3. **Configure build settings**
4. **Add environment variables**

**Detailed Setup:**

#### 1. Create Render Account
1. Sign up at https://render.com/
2. Connect your GitHub account

#### 2. Deploy Web Service
1. Click "New +" → "Web Service"
2. Connect your `shusrusha` repository
3. Configure:
   - **Name**: `shusrusha-app`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements-app.txt`
   - **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

#### 3. Add Environment Variables
1. In service settings, add:
   - `OPENAI_API_KEY`: your OpenAI API key
   - `PYTHON_VERSION`: 3.11

**Cost**: Free tier available, then $7/month

---

### Option 4: Heroku (Enterprise Grade)

**Steps:**
1. **Install Heroku CLI**
2. **Create Heroku app**
3. **Deploy with Git**
4. **Configure environment**

**Detailed Setup:**

#### 1. Prepare for Heroku
Create `Procfile` in your project root:
```
web: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

Create `runtime.txt`:
```
python-3.11.5
```

#### 2. Deploy to Heroku
```bash
# Install Heroku CLI first
heroku login
heroku create your-shusrusha-app
git push heroku main
```

#### 3. Set Environment Variables
```bash
heroku config:set OPENAI_API_KEY=your_openai_api_key_here
```

#### 4. Open Your App
```bash
heroku open
```

**Cost**: $7/month minimum

---

## 🔧 Required App Modifications

To make your app work well in cloud deployment, make these changes:

### 1. Update app.py for Cloud Deployment

Add this at the top of `app.py`:
```python
import os
import streamlit as st

# Cloud deployment configuration
st.set_page_config(
    page_title="Shusrusha - Medical Document Processor",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Check for API key
if not os.getenv("OPENAI_API_KEY"):
    st.error("⚠️ OpenAI API key not configured. Please contact the administrator.")
    st.stop()
```

### 2. Add Usage Tracking (Optional)

Add user tracking to monitor usage:
```python
import datetime
import json

def log_usage(user_info, action):
    """Log user activity for monitoring"""
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "user": user_info,
        "action": action
    }
    # Could save to file, database, or send to monitoring service
    print(f"Usage: {json.dumps(log_entry)}")

# Add to your processing functions:
log_usage(st.session_state.get("user_id", "anonymous"), "document_processed")
```

### 3. Add Rate Limiting (Recommended)

Prevent abuse of your API key:
```python
import time
from collections import defaultdict

# Simple rate limiting
usage_tracker = defaultdict(list)

def check_rate_limit(user_id, limit_per_hour=10):
    """Limit API calls per user"""
    now = time.time()
    hour_ago = now - 3600
    
    # Clean old entries
    usage_tracker[user_id] = [t for t in usage_tracker[user_id] if t > hour_ago]
    
    if len(usage_tracker[user_id]) >= limit_per_hour:
        return False
    
    usage_tracker[user_id].append(now)
    return True

# Use in your app:
if not check_rate_limit(st.session_state.get("user_id", "anonymous")):
    st.error("Rate limit exceeded. Please try again later.")
    st.stop()
```

## 📊 Monitoring Your Deployment

### 1. OpenAI Usage Dashboard
- Visit https://platform.openai.com/usage
- Monitor API calls and costs
- Set up billing alerts

### 2. Application Logs
Most platforms provide logging:
- **Streamlit Cloud**: View logs in app dashboard
- **Railway**: Logs tab in project dashboard  
- **Render**: Logs section in service
- **Heroku**: `heroku logs --tail`

### 3. User Analytics
Add Google Analytics or similar:
```python
# Add to app.py
st.components.v1.html("""
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
""", height=0)
```

## 🔒 Security Considerations

### 1. API Key Protection
- ✅ Never commit API keys to Git
- ✅ Use environment variables only
- ✅ Rotate keys periodically
- ✅ Monitor usage for anomalies

### 2. Access Control
Add simple authentication:
```python
def authenticate():
    """Simple password protection"""
    password = st.text_input("Password", type="password")
    if password != os.getenv("APP_PASSWORD", ""):
        st.error("Access denied")
        st.stop()

# Add at app start
authenticate()
```

### 3. Content Filtering
Add checks for appropriate content:
```python
def validate_upload(file):
    """Validate uploaded files"""
    if file.size > 10 * 1024 * 1024:  # 10MB limit
        st.error("File too large")
        return False
    
    if not file.type.startswith('image/'):
        st.error("Only image files allowed")
        return False
    
    return True
```

## 💰 Cost Management

### 1. Set OpenAI Usage Limits
1. Go to https://platform.openai.com/account/billing/limits
2. Set monthly usage limits
3. Add payment method with low limit

### 2. Monitor Costs
- Check OpenAI dashboard daily
- Set up email alerts for usage
- Consider implementing user quotas

### 3. Optimize API Usage
```python
# Cache results to avoid repeat processing
@st.cache_data(ttl=3600)  # Cache for 1 hour
def process_document_cached(file_hash):
    return process_document(file_hash)
```

## 🎯 Recommended Approach

**For Personal/Small Team Use:**
1. **Streamlit Cloud** (free, easy setup)
2. Add simple rate limiting
3. Monitor OpenAI usage weekly

**For Professional Use:**
1. **Railway or Render** (reliable, affordable)
2. Add authentication
3. Implement usage tracking
4. Set up monitoring alerts

**For Enterprise Use:**
1. **Heroku or AWS** (scalable, secure)
2. Full authentication system
3. Database for user management
4. Comprehensive monitoring

## 🚀 Quick Start

**Fastest deployment (5 minutes):**
1. Push code to GitHub
2. Go to https://share.streamlit.io/
3. Deploy your repository
4. Add OPENAI_API_KEY in secrets
5. Share the URL!

Your users can now access Shusrusha without any setup, and all API usage goes through your account. 🎉
