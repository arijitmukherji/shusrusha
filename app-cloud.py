"""
Shusrusha - Cloud Deployment Version
Enhanced with rate limiting, monitoring, and multi-user support
"""

import os
import streamlit as st
import time
import json
import hashlib
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List

# Cloud deployment configuration
st.set_page_config(
    page_title="Shusrusha - Medical Document Processor",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'mailto:support@yourcompany.com',
        'Report a bug': 'mailto:bugs@yourcompany.com',
        'About': """
        # Shusrusha Medical Document Processor
        
        Convert medical discharge summaries into interactive reports.
        
        **Version**: 2.0 Cloud Edition
        **Powered by**: OpenAI GPT Models
        """
    }
)

# Initialize session state for tracking
if 'user_id' not in st.session_state:
    st.session_state.user_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]

if 'usage_count' not in st.session_state:
    st.session_state.usage_count = 0

if 'last_reset' not in st.session_state:
    st.session_state.last_reset = datetime.now()

# Rate limiting configuration
RATE_LIMITS = {
    'documents_per_hour': int(os.getenv('RATE_LIMIT_DOCS_HOUR', '5')),
    'documents_per_day': int(os.getenv('RATE_LIMIT_DOCS_DAY', '20')),
    'max_file_size_mb': int(os.getenv('MAX_FILE_SIZE_MB', '10'))
}

# Usage tracking (in-memory for simplicity)
if 'usage_tracker' not in st.session_state:
    st.session_state.usage_tracker = defaultdict(list)

def check_api_key():
    """Verify OpenAI API key is configured"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("⚠️ **Service Unavailable**")
        st.error("The OpenAI API key is not configured. Please contact the administrator.")
        st.info("📧 Contact: support@yourcompany.com")
        st.stop()
    return api_key

def log_usage(user_id: str, action: str, details: Dict = None):
    """Log user activity for monitoring"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "action": action,
        "details": details or {}
    }
    
    # In production, you might want to send this to a logging service
    print(f"USAGE_LOG: {json.dumps(log_entry)}")
    
    # Store in session state for display
    if 'activity_log' not in st.session_state:
        st.session_state.activity_log = []
    
    st.session_state.activity_log.append(log_entry)
    
    # Keep only last 100 entries
    if len(st.session_state.activity_log) > 100:
        st.session_state.activity_log = st.session_state.activity_log[-100:]

def check_rate_limit(user_id: str) -> tuple[bool, str]:
    """Check if user has exceeded rate limits"""
    now = datetime.now()
    hour_ago = now - timedelta(hours=1)
    day_ago = now - timedelta(days=1)
    
    # Get user's usage history
    user_usage = st.session_state.usage_tracker[user_id]
    
    # Clean old entries
    user_usage = [timestamp for timestamp in user_usage if timestamp > day_ago]
    st.session_state.usage_tracker[user_id] = user_usage
    
    # Check hourly limit
    recent_usage = [timestamp for timestamp in user_usage if timestamp > hour_ago]
    if len(recent_usage) >= RATE_LIMITS['documents_per_hour']:
        return False, f"Rate limit exceeded: {RATE_LIMITS['documents_per_hour']} documents per hour. Try again in {60 - (now - max(recent_usage)).seconds // 60} minutes."
    
    # Check daily limit  
    if len(user_usage) >= RATE_LIMITS['documents_per_day']:
        return False, f"Daily limit exceeded: {RATE_LIMITS['documents_per_day']} documents per day. Try again tomorrow."
    
    return True, "OK"

def record_usage(user_id: str):
    """Record a successful document processing"""
    st.session_state.usage_tracker[user_id].append(datetime.now())
    st.session_state.usage_count += 1

def validate_file(uploaded_file) -> tuple[bool, str]:
    """Validate uploaded file"""
    if not uploaded_file:
        return False, "No file uploaded"
    
    # Check file size
    if uploaded_file.size > RATE_LIMITS['max_file_size_mb'] * 1024 * 1024:
        return False, f"File too large. Maximum size: {RATE_LIMITS['max_file_size_mb']}MB"
    
    # Check file type
    if not uploaded_file.type.startswith('image/'):
        return False, "Only image files are supported (JPG, PNG, etc.)"
    
    return True, "Valid"

def show_usage_stats():
    """Display usage statistics"""
    user_id = st.session_state.user_id
    user_usage = st.session_state.usage_tracker[user_id]
    
    now = datetime.now()
    hour_ago = now - timedelta(hours=1)
    day_ago = now - timedelta(days=1)
    
    recent_usage = [t for t in user_usage if t > hour_ago]
    daily_usage = [t for t in user_usage if t > day_ago]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "This Hour", 
            f"{len(recent_usage)}/{RATE_LIMITS['documents_per_hour']}", 
            delta=f"{RATE_LIMITS['documents_per_hour'] - len(recent_usage)} remaining"
        )
    
    with col2:
        st.metric(
            "Today", 
            f"{len(daily_usage)}/{RATE_LIMITS['documents_per_day']}", 
            delta=f"{RATE_LIMITS['documents_per_day'] - len(daily_usage)} remaining"
        )
    
    with col3:
        st.metric(
            "Session", 
            st.session_state.usage_count,
            delta="documents processed"
        )

def main():
    """Main application"""
    
    # Check API key first
    check_api_key()
    
    # Header
    st.title("🏥 Shusrusha Medical Document Processor")
    st.markdown("**Cloud Edition** - Convert discharge summaries into interactive reports")
    
    # Sidebar with info
    with st.sidebar:
        st.header("📊 Usage Dashboard")
        show_usage_stats()
        
        st.header("ℹ️ Information")
        st.info(f"""
        **User ID**: `{st.session_state.user_id}`
        
        **Rate Limits**:
        - {RATE_LIMITS['documents_per_hour']} documents/hour
        - {RATE_LIMITS['documents_per_day']} documents/day
        - {RATE_LIMITS['max_file_size_mb']}MB max file size
        
        **Features**:
        - OCR text extraction
        - Medical diagnosis extraction
        - Medication analysis
        - PharmeEasy integration
        - Interactive HTML reports
        """)
        
        if st.button("🔄 Reset Session"):
            for key in ['usage_count', 'activity_log']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["📄 Process Document", "📈 Activity Log", "ℹ️ Help"])
    
    with tab1:
        st.header("Upload Medical Document")
        
        # File upload
        uploaded_files = st.file_uploader(
            "Choose discharge summary images",
            type=['png', 'jpg', 'jpeg', 'pdf'],
            accept_multiple_files=True,
            help="Upload one or more images of medical discharge summaries"
        )
        
        if uploaded_files:
            # Validate each file
            valid_files = []
            for uploaded_file in uploaded_files:
                is_valid, message = validate_file(uploaded_file)
                if is_valid:
                    valid_files.append(uploaded_file)
                else:
                    st.error(f"❌ {uploaded_file.name}: {message}")
            
            if valid_files:
                st.success(f"✅ {len(valid_files)} valid file(s) ready for processing")
                
                # Processing options
                st.subheader("Processing Options")
                
                col1, col2 = st.columns(2)
                with col1:
                    run_ocr = st.checkbox("🔍 OCR Text Extraction", value=True, disabled=True)
                    run_diagnoses = st.checkbox("🏥 Extract Diagnoses", value=True)
                    
                with col2:
                    run_medications = st.checkbox("💊 Extract Medications", value=True)
                    run_pharmeasy = st.checkbox("🔗 PharmeEasy Integration", value=True)
                
                # Model selection
                model_choice = st.selectbox(
                    "🤖 AI Model",
                    ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
                    index=0,
                    help="gpt-4o-mini is faster and cheaper, gpt-4o is more accurate"
                )
                
                # Process button
                if st.button("🚀 Process Documents", type="primary"):
                    # Check rate limits
                    can_process, limit_message = check_rate_limit(st.session_state.user_id)
                    
                    if not can_process:
                        st.error(f"❌ {limit_message}")
                        log_usage(st.session_state.user_id, "rate_limit_hit", {"message": limit_message})
                    else:
                        # Record usage
                        record_usage(st.session_state.user_id)
                        
                        # Log processing start
                        log_usage(st.session_state.user_id, "processing_started", {
                            "file_count": len(valid_files),
                            "model": model_choice,
                            "options": {
                                "diagnoses": run_diagnoses,
                                "medications": run_medications,
                                "pharmeasy": run_pharmeasy
                            }
                        })
                        
                        # Process files (import and run your existing logic here)
                        try:
                            # This is where you'd import and call your existing processing functions
                            # For now, showing a placeholder
                            
                            with st.spinner("Processing documents..."):
                                time.sleep(2)  # Simulate processing
                                
                                # Placeholder results
                                st.success("✅ Processing completed!")
                                
                                # Show results tabs
                                result_tab1, result_tab2, result_tab3 = st.tabs(["📝 Markdown", "🌐 HTML Report", "📊 Analysis"])
                                
                                with result_tab1:
                                    st.code("# Sample OCR Output\n\nPatient discharge summary processed...", language="markdown")
                                    
                                with result_tab2:
                                    st.components.v1.html("<h3>Interactive HTML Report</h3><p>Sample interactive report would appear here...</p>", height=200)
                                    
                                with result_tab3:
                                    st.json({
                                        "diagnoses_found": 3,
                                        "medications_found": 5,
                                        "pharmeasy_matches": 4,
                                        "processing_time": "45 seconds",
                                        "model_used": model_choice
                                    })
                                
                                # Log successful completion
                                log_usage(st.session_state.user_id, "processing_completed", {
                                    "success": True,
                                    "processing_time": 45
                                })
                                
                        except Exception as e:
                            st.error(f"❌ Processing failed: {str(e)}")
                            log_usage(st.session_state.user_id, "processing_failed", {"error": str(e)})
    
    with tab2:
        st.header("📈 Activity Log")
        
        if 'activity_log' in st.session_state and st.session_state.activity_log:
            # Show recent activity
            st.subheader("Recent Activity")
            
            for entry in reversed(st.session_state.activity_log[-10:]):  # Show last 10
                timestamp = datetime.fromisoformat(entry['timestamp']).strftime("%H:%M:%S")
                action = entry['action'].replace('_', ' ').title()
                
                with st.expander(f"{timestamp} - {action}"):
                    st.json(entry)
        else:
            st.info("No activity recorded yet. Process a document to see activity logs.")
    
    with tab3:
        st.header("ℹ️ Help & Information")
        
        st.markdown("""
        ### 🎯 How to Use Shusrusha
        
        1. **Upload** medical discharge summary images (JPG, PNG, PDF)
        2. **Choose** processing options based on your needs
        3. **Select** AI model (gpt-4o-mini for speed, gpt-4o for accuracy)
        4. **Click** Process Documents
        5. **Download** results as HTML reports and markdown files
        
        ### 📋 Features
        
        - **OCR**: Extract text from medical document images
        - **Diagnosis Extraction**: Identify medical conditions and lab tests
        - **Medication Analysis**: Extract medications with dosages and instructions
        - **PharmeEasy Integration**: Find medication links and pricing
        - **Interactive Reports**: Generate clickable HTML summaries
        
        ### ⚡ Rate Limits
        
        To ensure fair usage and control costs:
        - **{} documents per hour** per user
        - **{} documents per day** per user
        - **{}MB maximum** file size
        
        ### 🔒 Privacy & Security
        
        - Your documents are processed securely
        - No personal data is stored permanently
        - API usage is monitored for cost control
        - All processing happens in secure cloud infrastructure
        
        ### 📞 Support
        
        Need help? Contact support at: **support@yourcompany.com**
        
        Report bugs at: **bugs@yourcompany.com**
        """.format(
            RATE_LIMITS['documents_per_hour'],
            RATE_LIMITS['documents_per_day'], 
            RATE_LIMITS['max_file_size_mb']
        ))

if __name__ == "__main__":
    main()
