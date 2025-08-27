# 🌐 Hybrid Cloud-Local Deployment Guide

This approach lets you deploy Streamlit to the cloud while keeping API keys and processing on your local machine.

## 🎯 Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Cloud Users   │───▶│  Cloud Streamlit │───▶│ Your Local API  │
│   (Web Browser) │    │   (Frontend UI)  │    │   (Backend)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              │                        │
                       ✅ Public Access          🔐 Your API Keys
                       ✅ No Setup Required      🔐 Full Control
                       ✅ Professional UI        🔐 Cost Management
```

## 🚀 Method 1: API Bridge Architecture

### Step 1: Create Local API Server

Create `local_api_server.py`:
```python
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import requests
import json

# Load your local environment
load_dotenv()

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from cloud app

# Your OpenAI API key stays local
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@app.route('/process', methods=['POST'])
def process_document():
    """Process document using local API key"""
    try:
        data = request.json
        
        # Extract parameters from cloud app
        image_data = data.get('image_data')
        processing_options = data.get('options', {})
        
        # Call OpenAI API using your local key
        # (Include your existing processing logic here)
        
        result = {
            "status": "success",
            "markdown": "# Sample processed text...",
            "diagnoses": {"conditions": ["Sample diagnosis"]},
            "medications": {"medications": ["Sample medication"]},
            "html_summary": "<h1>Sample HTML Report</h1>"
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "shusrusha-local-api"})

if __name__ == '__main__':
    # Run on your local network
    app.run(host='0.0.0.0', port=5000, debug=False)
```

### Step 2: Create Cloud Frontend App

Create `app_cloud_hybrid.py`:
```python
import streamlit as st
import requests
import json
import base64

st.set_page_config(
    page_title="Shusrusha - Medical Document Processor",
    page_icon="🏥",
    layout="wide"
)

# Configuration
LOCAL_API_URL = st.secrets.get("LOCAL_API_URL", "http://your-home-ip:5000")

def call_local_api(image_data, options):
    """Call your local API server"""
    try:
        response = requests.post(
            f"{LOCAL_API_URL}/process",
            json={
                "image_data": image_data,
                "options": options
            },
            timeout=300  # 5 minute timeout
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "error", "message": f"API returned {response.status_code}"}
    
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"Connection failed: {str(e)}"}

def main():
    st.title("🏥 Shusrusha Medical Document Processor")
    st.markdown("**Cloud Edition** - Powered by your local API")
    
    # Check local API connection
    try:
        health_response = requests.get(f"{LOCAL_API_URL}/health", timeout=5)
        if health_response.status_code == 200:
            st.success("✅ Connected to local processing server")
        else:
            st.error("❌ Local processing server not responding")
            st.stop()
    except:
        st.error("❌ Cannot connect to local processing server")
        st.info(f"Make sure your local server is running at: {LOCAL_API_URL}")
        st.stop()
    
    # File upload
    uploaded_files = st.file_uploader(
        "Upload medical documents",
        type=['png', 'jpg', 'jpeg'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        # Processing options
        col1, col2 = st.columns(2)
        with col1:
            extract_diagnoses = st.checkbox("Extract Diagnoses", value=True)
            extract_medications = st.checkbox("Extract Medications", value=True)
        with col2:
            pharmeasy_integration = st.checkbox("PharmeEasy Integration", value=True)
        
        if st.button("Process Documents", type="primary"):
            for uploaded_file in uploaded_files:
                # Convert image to base64
                image_data = base64.b64encode(uploaded_file.read()).decode()
                
                options = {
                    "diagnoses": extract_diagnoses,
                    "medications": extract_medications,
                    "pharmeasy": pharmeasy_integration
                }
                
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    result = call_local_api(image_data, options)
                    
                    if result["status"] == "success":
                        st.success(f"✅ Processed {uploaded_file.name}")
                        
                        # Display results
                        tab1, tab2, tab3 = st.tabs(["Markdown", "HTML Report", "Data"])
                        
                        with tab1:
                            st.markdown(result.get("markdown", "No markdown content"))
                        
                        with tab2:
                            st.components.v1.html(result.get("html_summary", "<p>No HTML content</p>"))
                        
                        with tab3:
                            st.json({
                                "diagnoses": result.get("diagnoses", {}),
                                "medications": result.get("medications", {})
                            })
                    else:
                        st.error(f"❌ Error processing {uploaded_file.name}: {result.get('message', 'Unknown error')}")

if __name__ == "__main__":
    main()
```

### Step 3: Setup Instructions

1. **Run Local API Server:**
```bash
# On your local machine
pip install flask flask-cors python-dotenv
python local_api_server.py
```

2. **Get Your Public IP:**
```bash
# Find your public IP
curl ifconfig.me
```

3. **Configure Router:**
   - Forward port 5000 to your local machine
   - Or use ngrok for easier setup

4. **Deploy Cloud App:**
   - Deploy `app_cloud_hybrid.py` to Streamlit Cloud
   - Set `LOCAL_API_URL` in secrets: `http://your-public-ip:5000`

## 🚀 Method 2: Ngrok Tunnel (Easiest)

### Step 1: Install Ngrok
```bash
# Download from https://ngrok.com/
# Or install via package manager
brew install ngrok  # macOS
```

### Step 2: Setup Local Server with Ngrok
```bash
# Run your local API server
python local_api_server.py

# In another terminal, create tunnel
ngrok http 5000
```

### Step 3: Update Cloud App
In Streamlit Cloud secrets:
```toml
LOCAL_API_URL = "https://abc123.ngrok.io"
```

## 🚀 Method 3: Webhook-Based Processing

Create `webhook_processor.py`:
```python
import streamlit as st
import requests
import time
import uuid

def process_via_webhook(image_data, webhook_url):
    """Send processing request to your local webhook"""
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Send request to your local webhook
    payload = {
        "job_id": job_id,
        "image_data": image_data,
        "callback_url": f"https://your-cloud-app.streamlit.app/callback/{job_id}"
    }
    
    response = requests.post(webhook_url, json=payload)
    
    if response.status_code == 200:
        # Poll for results
        for _ in range(60):  # Wait up to 5 minutes
            try:
                result_response = requests.get(f"https://your-cloud-app.streamlit.app/status/{job_id}")
                if result_response.status_code == 200:
                    result = result_response.json()
                    if result.get("status") == "completed":
                        return result
            except:
                pass
            
            time.sleep(5)
    
    return {"status": "error", "message": "Processing timeout or failed"}
```

## 💡 Method 4: Shared Database Approach

### Architecture:
1. **Cloud App** uploads documents to shared database
2. **Local Processor** polls database for new jobs
3. **Local Processor** processes using your API keys
4. **Local Processor** uploads results to database
5. **Cloud App** displays results

### Implementation:
```python
# Use services like:
# - Firebase Firestore
# - MongoDB Atlas
# - PostgreSQL on Heroku
# - Redis Cloud

import firebase_admin
from firebase_admin import credentials, firestore

# Cloud app uploads job
def submit_job(image_data):
    db = firestore.client()
    job_ref = db.collection('jobs').document()
    job_ref.set({
        'status': 'pending',
        'image_data': image_data,
        'created_at': firestore.SERVER_TIMESTAMP
    })
    return job_ref.id

# Local processor polls and processes
def process_jobs():
    while True:
        jobs = db.collection('jobs').where('status', '==', 'pending').limit(1).get()
        for job in jobs:
            # Process with your local API key
            result = process_document(job.get('image_data'))
            
            # Update with results
            job.reference.update({
                'status': 'completed',
                'result': result
            })
```

## 🔧 Setup Steps Summary

### For Ngrok Method (Recommended):

1. **Local Setup:**
```bash
# Install dependencies
pip install flask flask-cors python-dotenv ngrok

# Start local API server
python local_api_server.py

# Start ngrok tunnel
ngrok http 5000
```

2. **Cloud Deployment:**
   - Deploy `app_cloud_hybrid.py` to Streamlit Cloud
   - Add ngrok URL to secrets
   - Users access via cloud URL

3. **Benefits:**
   - ✅ Your API keys stay local
   - ✅ You control all processing
   - ✅ Users get cloud convenience
   - ✅ No API key sharing
   - ✅ Full cost control

## 🔒 Security Considerations

1. **API Authentication:**
```python
# Add API key authentication to local server
@app.before_request
def authenticate():
    auth_header = request.headers.get('Authorization')
    if auth_header != f"Bearer {LOCAL_API_SECRET}":
        return jsonify({"error": "Unauthorized"}), 401
```

2. **Rate Limiting:**
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)
```

3. **Input Validation:**
```python
def validate_request(data):
    if not data.get('image_data'):
        raise ValueError("No image data provided")
    
    # Check file size, format, etc.
    return True
```

## 💰 Cost Benefits

- ✅ **Full cost control** - All API usage through your account
- ✅ **No surprises** - Monitor usage in real-time
- ✅ **Flexible limits** - Set your own rate limits
- ✅ **Usage analytics** - Track who uses what

## 🚀 Quick Start

1. **Test locally first:**
```bash
python local_api_server.py
curl -X POST http://localhost:5000/health
```

2. **Setup ngrok:**
```bash
ngrok http 5000
# Note the HTTPS URL (e.g., https://abc123.ngrok.io)
```

3. **Deploy to Streamlit Cloud:**
   - Upload `app_cloud_hybrid.py`
   - Set `LOCAL_API_URL` in secrets to your ngrok URL
   - Share the cloud app URL with users

## 🚀 Quick Start Guide

### Option 1: Automated Setup (Recommended)

**For macOS/Linux:**
```bash
chmod +x setup_hybrid.sh
./setup_hybrid.sh
```

**For Windows:**
```cmd
setup_hybrid.bat
```

These scripts will:
1. ✅ Install dependencies
2. ✅ Create .env file with your API key
3. ✅ Start local API server
4. ✅ Create ngrok tunnel
5. ✅ Provide cloud app setup instructions

### Option 2: Manual Setup

#### Step 1: Install Dependencies
```bash
pip install -r requirements-local-api.txt
```

#### Step 2: Configure Environment
Create `.env` file:
```env
OPENAI_API_KEY=your_openai_api_key_here
LOCAL_API_SECRET=your_secret_key_here
```

#### Step 3: Start Local Server
```bash
python local_api_server.py
```

#### Step 4: Create Public Tunnel
```bash
# Install ngrok from https://ngrok.com/
ngrok http 5000
```

#### Step 5: Deploy Cloud App
1. Deploy `app_hybrid_cloud.py` to Streamlit Cloud
2. Add secrets:
   - `LOCAL_API_URL`: Your ngrok HTTPS URL
   - `LOCAL_API_SECRET`: Same as in your .env file

## 📁 File Overview

| File | Purpose | Location |
|------|---------|----------|
| `local_api_server.py` | Local API server with your keys | Your computer |
| `app_hybrid_cloud.py` | Cloud frontend for users | Streamlit Cloud |
| `requirements-local-api.txt` | Local server dependencies | Your computer |
| `setup_hybrid.sh/bat` | Automated setup scripts | Your computer |
