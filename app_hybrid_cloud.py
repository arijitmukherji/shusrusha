"""
Shusrusha Cloud Frontend
Connects to your local API server while providing cloud access for users
"""

import streamlit as st
import requests
import json
import base64
import time
from datetime import datetime
import hashlib

# Cloud app configuration
st.set_page_config(
    page_title="Shusrusha - Medical Document Processor",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration from Streamlit secrets
LOCAL_API_URL = st.secrets.get("LOCAL_API_URL", "http://localhost:5000")
LOCAL_API_SECRET = st.secrets.get("LOCAL_API_SECRET", "your-secret-key-here")
ENABLE_USAGE_TRACKING = st.secrets.get("ENABLE_USAGE_TRACKING", True)

# Session state initialization
if 'user_id' not in st.session_state:
    st.session_state.user_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]

if 'request_count' not in st.session_state:
    st.session_state.request_count = 0

def call_local_api(endpoint, data=None, method='GET'):
    """Call your local API server"""
    try:
        headers = {
            'Authorization': f'Bearer {LOCAL_API_SECRET}',
            'Content-Type': 'application/json'
        }
        
        url = f"{LOCAL_API_URL.rstrip('/')}/{endpoint.lstrip('/')}"
        
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=300)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        elif response.status_code == 401:
            return {"success": False, "error": "Authentication failed. Check API secret."}
        elif response.status_code == 429:
            return {"success": False, "error": "Rate limit exceeded. Please wait before trying again."}
        else:
            return {"success": False, "error": f"API returned status {response.status_code}: {response.text}"}
    
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timed out. Processing may take longer than expected."}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot connect to local processing server. Please check if it's running."}
    except Exception as e:
        return {"success": False, "error": f"Request failed: {str(e)}"}

def check_api_health():
    """Check if local API server is healthy"""
    result = call_local_api('health', method='GET')
    return result

def process_document(image_data, options, model='gpt-4o-mini'):
    """Process document via local API"""
    data = {
        'image_data': image_data,
        'options': options,
        'model': model
    }
    
    result = call_local_api('process', data=data, method='POST')
    
    if result['success']:
        st.session_state.request_count += 1
    
    return result

def log_usage(action, details=None):
    """Log usage for analytics"""
    if not ENABLE_USAGE_TRACKING:
        return
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": st.session_state.user_id,
        "action": action,
        "details": details or {}
    }
    
    # Store in session state
    if 'usage_log' not in st.session_state:
        st.session_state.usage_log = []
    
    st.session_state.usage_log.append(log_entry)
    
    # Keep only last 50 entries
    if len(st.session_state.usage_log) > 50:
        st.session_state.usage_log = st.session_state.usage_log[-50:]

def validate_file(uploaded_file):
    """Validate uploaded file"""
    max_size = 10 * 1024 * 1024  # 10MB
    
    if uploaded_file.size > max_size:
        return False, f"File too large. Maximum size: {max_size // (1024*1024)}MB"
    
    if not uploaded_file.type.startswith('image/'):
        return False, "Only image files are supported (JPG, PNG, etc.)"
    
    return True, "Valid"

def show_connection_status():
    """Show connection status to local API"""
    with st.sidebar:
        st.header("🔗 Connection Status")
        
        health_result = check_api_health()
        
        if health_result['success']:
            health_data = health_result['data']
            st.success("✅ Connected to local server")
            
            with st.expander("Server Details"):
                st.json({
                    "Status": health_data.get('status', 'Unknown'),
                    "OpenAI Configured": health_data.get('openai_key_configured', False),
                    "Server Time": health_data.get('timestamp', 'Unknown'),
                    "API URL": LOCAL_API_URL
                })
        else:
            st.error("❌ Cannot connect to local server")
            st.error(health_result['error'])
            
            with st.expander("Troubleshooting"):
                st.markdown("""
                **Common Issues:**
                1. Local server not running
                2. Wrong API URL in secrets
                3. Firewall blocking connection
                4. Wrong API secret key
                
                **Solutions:**
                1. Run: `python local_api_server.py`
                2. Check LOCAL_API_URL in app secrets
                3. If using ngrok, update the URL
                """)

def show_usage_stats():
    """Show usage statistics"""
    with st.sidebar:
        st.header("📊 Usage Stats")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Session Requests", st.session_state.request_count)
        with col2:
            st.metric("User ID", f"...{st.session_state.user_id[-4:]}")
        
        if st.button("🔄 Reset Stats"):
            st.session_state.request_count = 0
            if 'usage_log' in st.session_state:
                st.session_state.usage_log = []
            st.rerun()

def main():
    """Main application"""
    
    # Header
    st.title("🏥 Shusrusha Medical Document Processor")
    st.markdown("**Cloud Edition** - Powered by your local API server")
    
    # Sidebar
    show_connection_status()
    show_usage_stats()
    
    # Check if we can connect to local API
    health_result = check_api_health()
    if not health_result['success']:
        st.error("🚨 **Cannot connect to local processing server**")
        st.error(health_result['error'])
        
        st.markdown("### 🔧 Setup Instructions")
        st.markdown("""
        1. **Start your local server:**
           ```bash
           python local_api_server.py
           ```
        
        2. **If using ngrok for public access:**
           ```bash
           ngrok http 5000
           ```
           Then update `LOCAL_API_URL` in app secrets.
        
        3. **Check your secrets configuration:**
           - `LOCAL_API_URL`: Your server URL
           - `LOCAL_API_SECRET`: Authentication key
        """)
        
        return
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["📄 Process Documents", "📈 Activity Log", "ℹ️ Help"])
    
    with tab1:
        st.header("Upload Medical Documents")
        
        # File upload
        uploaded_files = st.file_uploader(
            "Choose discharge summary images",
            type=['png', 'jpg', 'jpeg'],
            accept_multiple_files=True,
            help="Upload one or more images of medical discharge summaries"
        )
        
        if uploaded_files:
            # Validate files
            valid_files = []
            for uploaded_file in uploaded_files:
                is_valid, message = validate_file(uploaded_file)
                if is_valid:
                    valid_files.append(uploaded_file)
                    st.success(f"✅ {uploaded_file.name} - {message}")
                else:
                    st.error(f"❌ {uploaded_file.name} - {message}")
            
            if valid_files:
                st.markdown("---")
                
                # Processing options
                st.subheader("🔧 Processing Options")
                
                col1, col2 = st.columns(2)
                with col1:
                    extract_diagnoses = st.checkbox("🏥 Extract Diagnoses", value=True)
                    extract_medications = st.checkbox("💊 Extract Medications", value=True)
                
                with col2:
                    pharmeasy_integration = st.checkbox("🔗 PharmeEasy Integration", value=True)
                    generate_html = st.checkbox("📄 Generate HTML Report", value=True)
                
                # Model selection
                model_choice = st.selectbox(
                    "🤖 AI Model",
                    ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
                    index=0,
                    help="gpt-4o-mini is faster and cheaper, gpt-4o is more accurate"
                )
                
                # Process button
                if st.button("🚀 Process Documents", type="primary"):
                    log_usage("processing_started", {
                        "file_count": len(valid_files),
                        "model": model_choice,
                        "options": {
                            "diagnoses": extract_diagnoses,
                            "medications": extract_medications,
                            "pharmeasy": pharmeasy_integration,
                            "html": generate_html
                        }
                    })
                    
                    # Process each file
                    for i, uploaded_file in enumerate(valid_files):
                        st.markdown(f"### Processing {uploaded_file.name}")
                        
                        # Convert to base64
                        image_data = base64.b64encode(uploaded_file.read()).decode()
                        
                        # Prepare options
                        options = {
                            "diagnoses": extract_diagnoses,
                            "medications": extract_medications,
                            "pharmeasy": pharmeasy_integration,
                            "html": generate_html
                        }
                        
                        # Process document
                        with st.spinner(f"Processing {uploaded_file.name}... This may take 1-2 minutes."):
                            result = process_document(image_data, options, model_choice)
                        
                        if result['success']:
                            result_data = result['data']
                            st.success(f"✅ Successfully processed {uploaded_file.name}")
                            
                            # Display results in tabs
                            result_tab1, result_tab2, result_tab3, result_tab4 = st.tabs([
                                "📝 Markdown", "🌐 HTML Report", "📊 Extracted Data", "🔧 Raw Response"
                            ])
                            
                            with result_tab1:
                                markdown_content = result_data.get('markdown', 'No markdown content available')
                                st.markdown("#### OCR Extracted Text")
                                st.markdown(markdown_content)
                                
                                # Download button
                                st.download_button(
                                    "📥 Download Markdown",
                                    markdown_content,
                                    file_name=f"{uploaded_file.name}_summary.md",
                                    mime="text/markdown"
                                )
                            
                            with result_tab2:
                                html_content = result_data.get('html_summary', '<p>No HTML content available</p>')
                                st.markdown("#### Interactive HTML Report")
                                st.components.v1.html(html_content, height=600, scrolling=True)
                                
                                # Download button
                                st.download_button(
                                    "📥 Download HTML Report",
                                    html_content,
                                    file_name=f"{uploaded_file.name}_report.html",
                                    mime="text/html"
                                )
                            
                            with result_tab3:
                                st.markdown("#### Extracted Medical Data")
                                
                                # Diagnoses
                                diagnoses = result_data.get('diagnoses', {})
                                if diagnoses:
                                    st.markdown("**🏥 Diagnoses:**")
                                    st.json(diagnoses)
                                
                                # Medications
                                medications = result_data.get('medications', {})
                                if medications:
                                    st.markdown("**💊 Medications:**")
                                    st.json(medications)
                                
                                # PharmeEasy matches
                                fixed_medications = result_data.get('fixed_medications', {})
                                if fixed_medications:
                                    st.markdown("**🔗 PharmeEasy Matches:**")
                                    st.json(fixed_medications)
                            
                            with result_tab4:
                                st.markdown("#### Raw API Response")
                                st.json(result_data)
                            
                            log_usage("processing_completed", {
                                "file_name": uploaded_file.name,
                                "success": True,
                                "model": model_choice
                            })
                        
                        else:
                            st.error(f"❌ Failed to process {uploaded_file.name}")
                            st.error(result['error'])
                            
                            log_usage("processing_failed", {
                                "file_name": uploaded_file.name,
                                "error": result['error']
                            })
                        
                        # Add separator between files
                        if i < len(valid_files) - 1:
                            st.markdown("---")
    
    with tab2:
        st.header("📈 Activity Log")
        
        if 'usage_log' in st.session_state and st.session_state.usage_log:
            st.subheader("Recent Activity")
            
            for entry in reversed(st.session_state.usage_log[-10:]):
                timestamp = datetime.fromisoformat(entry['timestamp']).strftime("%H:%M:%S")
                action = entry['action'].replace('_', ' ').title()
                
                with st.expander(f"{timestamp} - {action}"):
                    st.json(entry)
        else:
            st.info("No activity recorded yet. Process a document to see activity logs.")
    
    with tab3:
        st.header("ℹ️ Help & Information")
        
        st.markdown("""
        ### 🎯 How This Works
        
        This cloud app connects to **your local processing server** that runs on your computer with your API keys.
        
        **Benefits:**
        - ✅ Your API keys stay on your computer
        - ✅ You control all costs and usage
        - ✅ Users get easy cloud access
        - ✅ No need to share API keys
        
        ### 🔧 Setup Requirements
        
        1. **Local Server Running**: `python local_api_server.py`
        2. **Public Access**: Use ngrok or port forwarding
        3. **Configuration**: Set LOCAL_API_URL in app secrets
        
        ### 📋 Features
        
        - **OCR Text Extraction**: Convert images to markdown text
        - **Medical Analysis**: Extract diagnoses and medications
        - **PharmeEasy Integration**: Find medication links and pricing
        - **Interactive Reports**: Generate downloadable HTML summaries
        
        ### 🔒 Security
        
        - All processing happens on your local machine
        - API keys never leave your computer
        - Authentication required for API access
        - Rate limiting prevents abuse
        
        ### 📞 Support
        
        If you encounter issues:
        1. Check if local server is running
        2. Verify ngrok tunnel is active
        3. Check app secrets configuration
        4. Review server logs for errors
        """)

if __name__ == "__main__":
    main()
