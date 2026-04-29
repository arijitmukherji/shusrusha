#!/usr/bin/env python3
"""
Shusrusha Medical Document Processor - Standalone Web Application
A medical document processing app that converts discharge summary images 
into interactive HTML reports with medication links and analysis.
"""

import streamlit as st
import os
import tempfile
import base64
from pathlib import Path
from dotenv import load_dotenv
from langgraph_app import app_graph
import zipfile
import io
from datetime import datetime

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Shusrusha Medical Document Processor",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2E8B57;
        padding: 1rem 0;
        border-bottom: 2px solid #2E8B57;
        margin-bottom: 2rem;
    }
    .step-header {
        background: linear-gradient(90deg, #2E8B57, #32CD32);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
        .info-box {
        background: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .file-manager-modal {
        background: #f8f9fa;
        border: 2px solid #dee2e6;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .file-item {
        background: white;
        border: 1px solid #e9ecef;
        border-radius: 5px;
        padding: 0.5rem;
        margin: 0.25rem 0;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .compact-uploader {
        padding: 0.5rem;
        border: 2px dashed #6c757d;
        border-radius: 5px;
        text-align: center;
        background: #f8f9fa;
    }
    .instructions-modal {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .diagnosis-item {
        background: linear-gradient(135deg, #d4edda, #c3e6cb);
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        font-weight: 500;
    }
        .lab-test-item {
        background: linear-gradient(135deg, #d1ecf1, #bee5eb);
        border: 1px solid #bee5eb;
        border-radius: 8px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        font-weight: 500;
    }
    .processing-logs-modal {
        background: #f8f9fa;
        border: 2px solid #dee2e6;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        max-height: 400px;
        overflow-y: auto;
    }
    .log-entry {
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-radius: 5px;
        font-size: 0.9rem;
    }
    .medication-card {
        background: linear-gradient(135deg, #fff3cd, #ffeaa7);
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.75rem 0;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
    }
    .medication-card-high {
        background: linear-gradient(135deg, #d4edda, #c3e6cb);
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.75rem 0;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
    }
    .medication-card-medium {
        background: linear-gradient(135deg, #fff3cd, #ffeaa7);
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.75rem 0;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
    }
    .medication-card-low {
        background: linear-gradient(135deg, #f8d7da, #f5c6cb);
        border: 1px solid #f5c6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.75rem 0;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
    }
    .file-count-button {
        background: none !important;
        border: none !important;
        color: #0066cc !important;
        text-decoration: underline !important;
        cursor: pointer !important;
        font-size: 0.9rem !important;
        padding: 0 !important;
    }
    .file-count-button:hover {
        color: #004499 !important;
        text-decoration: none !important;
    }
</style>""", unsafe_allow_html=True)

# ── Enhanced design system override ─────────────────────────────────────────
st.markdown("""
<style>
    /* Design tokens */
    :root {
        --brand:       #1a8754;
        --brand-light: #d1f0e0;
        --brand-dark:  #145f3c;
        --warn:        #f59e0b;
        --danger:      #dc3545;
        --surface:     #ffffff;
        --surface-alt: #f8fafb;
        --border:      #e2e8f0;
        --text:        #1e293b;
        --text-muted:  #64748b;
        --radius:      10px;
        --shadow-sm:   0 1px 3px rgba(0,0,0,.07);
        --shadow-md:   0 4px 12px rgba(0,0,0,.10);
    }

    /* Page background */
    .stApp { background: #f0f4f8 !important; }

    /* Remove default Streamlit top padding */
    .block-container { padding-top: 1rem !important; }

    /* ── App header ── */
    .app-header {
        background: linear-gradient(135deg, #145f3c 0%, #1a8754 55%, #22c55e 100%);
        border-radius: var(--radius);
        padding: 1.4rem 2rem;
        margin-bottom: 1.5rem;
        color: white;
        box-shadow: var(--shadow-md);
    }
    .app-header h1 { color: white !important; margin: 0 0 .25rem; font-size: 1.75rem; font-weight: 700; }
    .app-header p  { color: rgba(255,255,255,.85); margin: 0; font-size: 0.9rem; }

    /* ── Section headings ── */
    .section-label {
        font-size: 0.68rem; font-weight: 700; letter-spacing: .08em;
        text-transform: uppercase; color: var(--text-muted); margin: 1.1rem 0 .4rem;
    }

    /* ── Cards ── */
    .card {
        background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius); padding: 1rem 1.2rem;
        margin-bottom: .75rem; box-shadow: var(--shadow-sm);
    }

    /* ── Medication card ── */
    .med-card {
        background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius); padding: .9rem 1.1rem;
        margin-bottom: .6rem; box-shadow: var(--shadow-sm);
        transition: box-shadow .15s ease;
    }
    .med-card:hover { box-shadow: var(--shadow-md); }
    .med-card-high   { border-left: 4px solid var(--brand); }
    .med-card-medium { border-left: 4px solid var(--warn); }
    .med-card-low    { border-left: 4px solid var(--danger); }
    .med-name  { font-size: 1rem; font-weight: 700; color: var(--brand-dark); margin-bottom: .35rem; }
    .med-meta  { display: flex; flex-wrap: wrap; gap: .4rem 1.1rem; font-size: .85rem; color: var(--text-muted); }
    .med-meta strong { color: var(--text); }

    /* ── Confidence badge ── */
    .badge { display: inline-block; padding: .15rem .55rem; border-radius: 999px;
             font-size: .72rem; font-weight: 700; color: white; vertical-align: middle; }
    .badge-high   { background: var(--brand); }
    .badge-medium { background: var(--warn); }
    .badge-low    { background: var(--danger); }

    /* ── Diagnosis / Lab chips ── */
    .chip { display: inline-block; padding: .25rem .65rem; border-radius: 999px;
            font-size: .82rem; font-weight: 500; margin: .15rem; }
    .chip-green { background: var(--brand-light); color: var(--brand-dark); }
    .chip-blue  { background: #dbeafe; color: #1d4ed8; }

    /* ── Metric cards ── */
    [data-testid="stMetric"] {
        background: var(--surface) !important; border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important; padding: .6rem .8rem !important;
        box-shadow: var(--shadow-sm) !important;
    }
    [data-testid="stMetricLabel"] { font-size: .78rem !important; color: var(--text-muted) !important; }
    [data-testid="stMetricValue"] { font-size: 1.45rem !important; color: var(--text) !important; font-weight: 700 !important; }

    /* ── Progress bar ── */
    [data-testid="stProgressBar"] > div > div { background: var(--brand) !important; border-radius: 4px; }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 2px solid var(--border); }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px 6px 0 0; padding: .4rem .9rem;
        font-size: .85rem; font-weight: 500; color: var(--text-muted);
        background: transparent; border: 1px solid transparent;
    }
    .stTabs [aria-selected="true"] {
        color: var(--brand-dark) !important; background: var(--surface) !important;
        border-color: var(--border) !important; border-bottom-color: white !important;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] { background: #f8fafb !important; border-right: 1px solid var(--border); }
    [data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color: var(--brand-dark) !important; }

    /* ── Buttons ── */
    .stButton > button[kind="primary"] {
        background: var(--brand) !important; border-color: var(--brand) !important;
        font-weight: 600 !important; border-radius: 8px !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: var(--brand-dark) !important; border-color: var(--brand-dark) !important;
    }
    .stButton > button:not([kind="primary"]) { border-radius: 8px !important; }

    /* ── File uploader ── */
    [data-testid="stFileUploader"] section {
        border: 2px dashed var(--border) !important;
        border-radius: var(--radius) !important;
        background: var(--surface-alt) !important;
    }
    [data-testid="stFileUploader"] section:hover {
        border-color: var(--brand) !important; background: var(--brand-light) !important;
    }

    /* ── Spinner override ── */
    .stSpinner > div { border-top-color: var(--brand) !important; }
</style>""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown("""
    <div class="app-header">
        <div>
            <h1>🏥 Shusrusha</h1>
            <p>AI-powered discharge summary processor — extract diagnoses, medications &amp; pharmacy links from images</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # API Key check and prompt (global for main)
    _env_key = os.getenv('OPENAI_API_KEY', '').strip()
    api_key = _env_key if _env_key else None
    with st.sidebar:
        st.markdown("### 🏥 Shusrusha")
        st.markdown('<div class="section-label">API</div>', unsafe_allow_html=True)
        if api_key:
            st.success("✅ API Key ready", icon="🔑")
        else:
            api_key = st.text_input(
                "OpenAI API Key",
                type="password",
                placeholder="sk-...",
                help="Kept in memory only — not saved to disk."
            )
            if not api_key:
                st.info("Enter your OpenAI API key above to get started.")
                st.stop()
            st.success("✅ API Key accepted")

        st.markdown('<div class="section-label">AI Models</div>', unsafe_allow_html=True)
        ocr_model = st.selectbox(
            "OCR (image → text)",
            ["gpt-5.4", "gpt-5.4-mini"],
            index=0,
            help="Higher model = better accuracy on handwritten/complex documents"
        )
        extraction_model = st.selectbox(
            "Extraction (diagnoses & meds)",
            ["gpt-5.4", "gpt-5.4-mini"],
            index=1,
            help="Model used for extracting structured data from OCR text"
        )
        pharmacy_model = st.selectbox(
            "Pharmacy matching",
            ["gpt-5.4", "gpt-5.4-mini"],
            index=1,
            help="Model used to match medications with PharmeEasy products"
        )

        st.markdown('<div class="section-label">Pipeline Steps</div>', unsafe_allow_html=True)
        run_diagnoses  = st.checkbox("🩺 Diagnoses",         value=True, help="Extract medical conditions and diagnoses")
        run_medications = st.checkbox("💊 Medications",       value=True, help="Extract medication names, strengths, instructions and duration")
        run_pharmacy   = st.checkbox("🔗 PharmeEasy links",  value=True, help="Match medications with pharmacy product links")
        run_summary    = st.checkbox("📋 HTML report",        value=True, help="Generate the final interactive HTML summary")

        if run_pharmacy and not run_medications:
            st.warning("⚠️ PharmeEasy requires Medications to be enabled.")

        st.markdown('<div class="section-label">Output</div>', unsafe_allow_html=True)
        save_files = st.checkbox("💾 Save files to disk", value=True, help="Save discharge.md and summary.html")
        show_debug = st.checkbox("🐛 Debug mode",         value=False, help="Show raw JSON and verbose logs")
        open_files = False  # opening files on server-side is not useful in web app
        
        if run_summary and not (run_medications or run_diagnoses):
            st.info("💡 HTML summary is richer with diagnoses and medications enabled.")

        st.markdown("---")
        st.markdown('<p style="font-size:.75rem;color:#94a3b8;text-align:center;">Shusrusha · Powered by OpenAI</p>', unsafe_allow_html=True)

    # ── Main content ────────────────────────────────────────────────────────
    # Initialize session state
    if 'selected_files' not in st.session_state:
        st.session_state.selected_files = []
    if not isinstance(st.session_state.selected_files, list):
        st.session_state.selected_files = []
    if 'last_uploader_state' not in st.session_state:
        st.session_state.last_uploader_state = []

    # File upload
    uploaded_files = st.file_uploader(
        "📂 Upload discharge summary images",
        type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'],
        accept_multiple_files=True,
        key="functional_file_uploader",
        help="Drag & drop or click. Supported: PNG, JPG, JPEG, GIF, BMP, TIFF"
    )

    # Track state changes — new selection replaces previous
    current_uploader_files = uploaded_files if uploaded_files else []
    current_file_names = [f.name for f in current_uploader_files]
    if current_file_names != st.session_state.last_uploader_state:
        st.session_state.selected_files = list(current_uploader_files)
        st.session_state.last_uploader_state = current_file_names

    # File summary row
    if st.session_state.selected_files:
        names = sorted(f.name for f in st.session_state.selected_files)
        count = len(names)
        st.markdown(
            f'<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;'
            f'padding:.5rem .85rem;font-size:.85rem;color:#166534;margin-bottom:.5rem;">'
            f'<strong>{count} file{"s" if count != 1 else ""} ready:</strong> {", ".join(names)}'
            f'</div>',
            unsafe_allow_html=True
        )

    # File validation
    uploaded_files = st.session_state.selected_files
    if uploaded_files:
        valid_files = [f for f in uploaded_files if f.size > 0]
        invalid_files = [f.name for f in uploaded_files if f.size == 0]
        if invalid_files:
            st.warning(f"⚠️ Skipping empty files: {', '.join(invalid_files)}")
        if not valid_files:
            uploaded_files = None
        else:
            uploaded_files = valid_files
    else:
        uploaded_files = None

    # How-to expander (replaces the old toggle-button modal)
    with st.expander("📖 How to use"):
        st.markdown("""
**Steps:**
1. Upload one or more discharge summary images above
2. Optionally adjust AI models and pipeline steps in the sidebar
3. Click **Start Processing** — results appear below when done
4. Download the interactive HTML report or individual files

**Tips:**
- Use **gpt-5.4** for OCR on handwritten or low-quality scans
- Upload multi-page documents as separate image files, in order
- Enable **Debug mode** in the sidebar to inspect raw extracted data
        """)

    # ── Processing section ──────────────────────────────────────────────────
    if uploaded_files:
        st.markdown("---")

        # Initialize processing state variables
        if 'processing_completed' not in st.session_state:
            st.session_state.processing_completed = False
        if 'processing_logs' not in st.session_state:
            st.session_state.processing_logs = []
        if 'show_processing_logs' not in st.session_state:
            st.session_state.show_processing_logs = False

        # Create a placeholder container for processing output that can be cleared
        processing_container = st.empty()

        # Show different buttons based on processing state
        if not st.session_state.processing_completed:
            with processing_container.container():
                if st.button("🚀 Start Processing", type="primary", use_container_width=True):
                    # Reset processing state for new run
                    st.session_state.processing_logs = []
                    st.session_state.processing_completed = False
                    st.session_state.show_processing_logs = False

                    with st.container():
                        process_documents(uploaded_files, ocr_model, extraction_model, pharmacy_model,
                                          save_files, open_files, show_debug,
                                          run_diagnoses, run_medications, run_pharmacy, run_summary,
                                          api_key, processing_container)
        else:
            with processing_container.container():
                col_done, col_logs, col_reprocess = st.columns([2, 2, 1])
                with col_done:
                    st.success("✅ Processing complete")
                with col_logs:
                    if st.button("📋 View logs", use_container_width=True):
                        st.session_state.show_processing_logs = not st.session_state.show_processing_logs
                with col_reprocess:
                    if st.button("🔄 Redo", type="primary", use_container_width=True):
                        st.session_state.processing_completed = False
                        st.session_state.processing_logs = []
                        st.session_state.show_processing_logs = False
                        st.rerun()

        # Processing logs (collapsible)
        if st.session_state.show_processing_logs and st.session_state.processing_logs:
            with st.expander("📋 Processing logs", expanded=True):
                for log_entry in st.session_state.processing_logs:
                    ts = log_entry.get('timestamp', '')
                    msg = log_entry['message']
                    if log_entry['type'] == 'success':
                        st.markdown(f"`{ts}` ✅ {msg}")
                    elif log_entry['type'] == 'warning':
                        st.markdown(f"`{ts}` ⚠️ {msg}")
                    elif log_entry['type'] == 'error':
                        st.markdown(f"`{ts}` ❌ {msg}")
                    else:
                        st.markdown(f"`{ts}` {msg}")

    # Display results progressively as processing steps complete
    if 'processing_results' in st.session_state and st.session_state.processing_results:
        display_results()

def add_processing_log(message, log_type="info"):
    """Add a message to the processing logs"""
    if 'processing_logs' not in st.session_state:
        st.session_state.processing_logs = []
    
    st.session_state.processing_logs.append({
        'message': message,
        'type': log_type,
        'timestamp': str(datetime.now().strftime("%H:%M:%S"))
    })

def process_documents(uploaded_files, ocr_model, extraction_model, pharmacy_model, save_files, open_files, show_debug, 
                     run_diagnoses, run_medications, run_pharmacy, run_summary, api_key, processing_container=None):
    """Process the uploaded documents through the entire pipeline"""
    
    # Initialize session state for results
    if 'processing_results' not in st.session_state:
        st.session_state.processing_results = {}
    
    try:
        add_processing_log("🚀 Starting document processing...", "info")
        
        # Validate uploaded files
        valid_files = [f for f in uploaded_files if f.size > 0]
        if not valid_files:
            add_processing_log("❌ No valid files to process. Please upload valid image files.", "error")
            st.error("❌ No valid files to process. Please upload valid image files.")
            return
        
        if len(valid_files) != len(uploaded_files):
            msg = f"⚠️ Processing {len(valid_files)} valid files out of {len(uploaded_files)} uploaded."
            add_processing_log(msg, "warning")
            st.warning(msg)
        
        # Create temporary directory for uploaded files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Save uploaded files to temporary directory
            image_paths = []
            for uploaded_file in valid_files:
                file_path = temp_path / uploaded_file.name
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                image_paths.append(str(file_path))
            
            msg = f"📁 Processing {len(image_paths)} image files..."
            add_processing_log(msg, "info")
            st.info(msg)
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: OCR
            step_msg = "🔍 Step 1/5: Processing OCR..."
            add_processing_log(step_msg, "info")
            status_text.text(step_msg)
            progress_bar.progress(0.2)
            
            with st.spinner("Extracting text from images..."):
                markdown = app_graph.run_node("OCR", image_paths, ocr_model, api_key=api_key)
                
                # Clean markdown
                markdown = clean_markdown(markdown)
                
                if save_files:
                    save_file("discharge.md", markdown)
                    success_msg = "✅ Markdown saved to discharge.md"
                    add_processing_log(success_msg, "success")
                    st.success(success_msg)
                    
                    if open_files:
                        open_result = open_file_in_system("discharge.md")
                        info_msg = f"📂 {open_result}"
                        add_processing_log(info_msg, "info")
                        st.info(info_msg)
                
                st.session_state.processing_results['markdown'] = markdown
                add_processing_log("✅ OCR processing completed successfully", "success")
            
            if show_debug:
                with st.expander("📄 OCR Results"):
                    st.markdown(markdown)
            
            # Step 2: Extract Diagnoses (Optional)
            if run_diagnoses:
                step_msg = "🩺 Step 2/5: Extracting diagnoses..."
                add_processing_log(step_msg, "info")
                status_text.text(step_msg)
                progress_bar.progress(0.4)
                
                with st.spinner("Extracting medical diagnoses..."):
                    diagnoses = app_graph.run_node("ExtractDiagnoses", model=extraction_model, api_key=api_key)
                    st.session_state.processing_results['diagnoses'] = diagnoses
                    add_processing_log("✅ Diagnoses extraction completed", "success")
                
                if show_debug:
                    with st.expander("🩺 Diagnosed Conditions"):
                        st.json(diagnoses)
            else:
                skip_msg = "⏭️ Skipping diagnoses extraction"
                add_processing_log(skip_msg, "info")
                st.info(skip_msg)
                st.session_state.processing_results['diagnoses'] = None
            
            # Step 3: Extract Medications (Optional)
            if run_medications:
                step_msg = "💊 Step 3/5: Extracting medications with strength and dosage..."
                add_processing_log(step_msg, "info")
                status_text.text(step_msg)
                progress_bar.progress(0.6)
                
                with st.spinner("Extracting medications..."):
                    medications = app_graph.run_node("ExtractMedications", model=extraction_model, api_key=api_key)
                    st.session_state.processing_results['medications'] = medications
                    add_processing_log("✅ Medications extraction completed", "success")
                
                if show_debug:
                    with st.expander("💊 Extracted Medications"):
                        st.json(medications)
            else:
                skip_msg = "⏭️ Skipping medications extraction"
                add_processing_log(skip_msg, "info")
                st.info(skip_msg)
                st.session_state.processing_results['medications'] = None
            
            # Step 4: Fix Medications (Optional, depends on medications)
            if run_pharmacy:
                if run_medications:
                    step_msg = "🔗 Step 4/5: Matching medications with PharmeEasy..."
                    add_processing_log(step_msg, "info")
                    status_text.text(step_msg)
                    progress_bar.progress(0.8)
                    
                    with st.spinner("Finding medication links..."):
                        fixed_medications = app_graph.run_node("FixMedications", model=pharmacy_model, api_key=api_key)
                        st.session_state.processing_results['fixed_medications'] = fixed_medications
                        add_processing_log("✅ PharmeEasy integration completed", "success")
                    
                    if show_debug:
                        with st.expander("🔗 Medication Links"):
                            st.json(fixed_medications)
                else:
                    warning_msg = "⚠️ Cannot run PharmeEasy integration - medications extraction is disabled"
                    add_processing_log(warning_msg, "warning")
                    st.warning(warning_msg)
                    st.session_state.processing_results['fixed_medications'] = None
            else:
                skip_msg = "⏭️ Skipping PharmeEasy integration"
                add_processing_log(skip_msg, "info")
                st.info(skip_msg)
                st.session_state.processing_results['fixed_medications'] = None
            
            # Step 5: Generate Summary (Optional)
            if run_summary:
                step_msg = "📋 Step 5/5: Generating interactive summary..."
                add_processing_log(step_msg, "info")
                status_text.text(step_msg)
                progress_bar.progress(1.0)
                
                with st.spinner("Creating interactive HTML report..."):
                    html_summary = app_graph.run_node("AddSummaryPills", api_key=api_key)
                    
                    if save_files:
                        save_file("summary.html", html_summary)
                        success_msg = "✅ HTML summary saved to summary.html"
                        add_processing_log(success_msg, "success")
                        st.success(success_msg)
                        
                        if open_files:
                            open_result = open_file_in_system("summary.html")
                            info_msg = f"📂 {open_result}"
                            add_processing_log(info_msg, "info")
                            st.info(info_msg)
                    
                    st.session_state.processing_results['html_summary'] = html_summary
                    add_processing_log("✅ HTML summary generation completed", "success")
            else:
                skip_msg = "⏭️ Skipping HTML summary generation"
                add_processing_log(skip_msg, "info")
                st.info(skip_msg)
                st.session_state.processing_results['html_summary'] = None
            
            # Final completion
            final_msg = "✅ Processing completed successfully!"
            add_processing_log(final_msg, "success")
            status_text.text(final_msg)
            
            # Set completion state 
            st.session_state.processing_completed = True
            add_processing_log("🎉 All processing steps completed successfully!", "success")
            
            # Clear the processing container to hide all the processing output
            if processing_container:
                processing_container.empty()
            
            # Trigger rerun to show the completed state
            st.rerun()
            
    except Exception as e:
        error_msg = f"❌ Error during processing: {str(e)}"
        add_processing_log(error_msg, "error")
        st.error(error_msg)
        st.session_state.processing_completed = True  # Mark as completed even if failed so user can view logs
        
        # Clear the processing container
        if processing_container:
            processing_container.empty()
        
        if show_debug:
            st.exception(e)
        
        # Trigger rerun to show the completed state
        st.rerun()
        
        # Clear the processing container and trigger rerun
        if processing_container:
            processing_container.empty()
        st.rerun()

def clean_markdown(markdown):
    """Clean up markdown text by removing code block wrappers"""
    if markdown.startswith("```markdown\n"):
        markdown = markdown[12:]  # Remove "```markdown\n"
    if markdown.endswith("\n```"):
        markdown = markdown[:-4]  # Remove "\n```"
    elif markdown.endswith("```"):
        markdown = markdown[:-3]  # Remove "```"
    
    # Also handle case where it starts with just ```
    if markdown.startswith("```\n"):
        markdown = markdown[4:]  # Remove "```\n"
    
    return markdown

def save_file(filename, content):
    """Save content to file and optionally open it"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

def open_file_in_system(filename):
    """Open file in the default system application"""
    import subprocess
    import sys
    try:
        if sys.platform == "darwin":  # macOS
            subprocess.run(["open", filename], check=True)
            return f"Opened {filename} in default application"
        elif sys.platform == "win32":  # Windows
            subprocess.run(["start", filename], shell=True, check=True)
            return f"Opened {filename} in default application"
        else:  # Linux
            subprocess.run(["xdg-open", filename], check=True)
            return f"Opened {filename} in default application"
    except subprocess.CalledProcessError as e:
        return f"Could not open {filename} automatically: {e}"
    except FileNotFoundError:
        return f"Could not find system command to open {filename}"

def display_results():
    """Display processing results in tabs."""
    if 'processing_results' not in st.session_state:
        return

    results = st.session_state.processing_results
    if not any(results.values()):
        return

    st.markdown("---")
    st.markdown("## 📊 Results")

    # Build tab list dynamically
    available_tabs, tab_labels = [], []
    available_tabs.append("summary");        tab_labels.append("📋 Summary")
    if results.get('markdown'):              available_tabs.append("markdown");      tab_labels.append("📄 OCR Text")
    if results.get('diagnoses') is not None: available_tabs.append("diagnoses");     tab_labels.append("🩺 Diagnoses")
    if results.get('medications') is not None: available_tabs.append("medications"); tab_labels.append("💊 Medications")
    if results.get('fixed_medications') is not None: available_tabs.append("medication_links"); tab_labels.append("🔗 Pharmacy Links")

    tab_containers = st.tabs(tab_labels) if len(available_tabs) > 1 else [st.container()]

    for tab_type, container in zip(available_tabs, tab_containers):
        with container:

            # ── Summary ──────────────────────────────────────────────────
            if tab_type == "summary":
                if results.get('html_summary'):
                    st.components.v1.html(results['html_summary'], height=620, scrolling=True)
                    st.download_button("📥 Download HTML Report", data=results['html_summary'],
                                       file_name="discharge_summary.html", mime="text/html",
                                       use_container_width=True)
                else:
                    st.info("HTML summary was skipped. Enable **HTML report** in the sidebar and reprocess.")
                    items = []
                    if results.get('markdown'):        items.append("✅ OCR Text")
                    if results.get('diagnoses'):       items.append("✅ Diagnoses")
                    if results.get('medications'):     items.append("✅ Medications")
                    if results.get('fixed_medications'): items.append("✅ Pharmacy Links")
                    if items:
                        st.markdown("Available: " + "  ·  ".join(items))

            # ── OCR Markdown ─────────────────────────────────────────────
            elif tab_type == "markdown":
                st.markdown(results['markdown'])
                st.download_button("📥 Download Markdown", data=results['markdown'],
                                   file_name="discharge.md", mime="text/markdown",
                                   use_container_width=True)

            # ── Diagnoses ─────────────────────────────────────────────────
            elif tab_type == "diagnoses":
                d = results['diagnoses']
                diag_list = d.get('diagnoses', [])
                lab_list  = d.get('lab_tests', [])

                c1, c2, c3 = st.columns(3)
                c1.metric("🩺 Diagnoses", len(diag_list))
                c2.metric("🧪 Lab Tests", len(lab_list))
                c3.metric("📊 Total", len(diag_list) + len(lab_list))
                st.markdown("---")

                col_d, col_l = st.columns(2)
                with col_d:
                    st.markdown("**🩺 Diagnoses**")
                    if diag_list:
                        chips = "".join(f'<span class="chip chip-green">{x}</span>' for x in diag_list)
                        st.markdown(f'<div style="line-height:2">{chips}</div>', unsafe_allow_html=True)
                    else:
                        st.caption("None found")
                with col_l:
                    st.markdown("**🧪 Lab Tests**")
                    if lab_list:
                        chips = "".join(f'<span class="chip chip-blue">{x}</span>' for x in lab_list)
                        st.markdown(f'<div style="line-height:2">{chips}</div>', unsafe_allow_html=True)
                    else:
                        st.caption("None found")

                with st.expander("🔍 Raw JSON"):
                    st.json(d)

            # ── Medications ───────────────────────────────────────────────
            elif tab_type == "medications":
                meds = results['medications'].get('medications', [])
                with_dur = len([m for m in meds if m.get('duration','').lower() not in ['','continue','as needed']])
                as_needed = len([m for m in meds if 'as needed' in m.get('duration','').lower()])

                c1, c2, c3 = st.columns(3)
                c1.metric("💊 Medications", len(meds))
                c2.metric("⏰ With Duration", with_dur)
                c3.metric("🔄 As Needed", as_needed)
                st.markdown("---")

                for i, med in enumerate(meds, 1):
                    st.markdown(f"""
                    <div class="med-card med-card-high">
                        <div class="med-name">💊 {i}. {med.get('name','Unknown')}</div>
                        <div class="med-meta">
                            <span><strong>Form</strong> {med.get('form','—')}</span>
                            <span><strong>Strength</strong> {med.get('strength','—')}</span>
                            <span><strong>Instructions</strong> {med.get('instructions','—')}</span>
                            <span><strong>Duration</strong> {med.get('duration','—')}</span>
                        </div>
                    </div>""", unsafe_allow_html=True)

                with st.expander("🔍 Raw JSON"):
                    st.json(results['medications'])

            # ── Pharmacy Links ────────────────────────────────────────────
            elif tab_type == "medication_links":
                fixed = results['fixed_medications']
                fixed_list = fixed.get('medications', [])
                hi   = len([m for m in fixed_list if m.get('selection_confidence', 0) > 80])
                lnks = len([m for m in fixed_list if m.get('pharmaeasy_url')])
                none = len([m for m in fixed_list if not m.get('all_products')])

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("💊 Total",         len(fixed_list))
                c2.metric("✅ High confidence", hi,   help=">80% match confidence")
                c3.metric("🔗 With links",     lnks)
                c4.metric("❌ No match",       none)
                st.markdown("---")

                for i, med in enumerate(fixed_list, 1):
                    conf = med.get('selection_confidence', 0)
                    url  = med.get('pharmaeasy_url') or (med.get('all_products') or [{}])[0].get('url', '')
                    card_cls = "med-card-high" if conf > 80 else "med-card-medium" if conf > 50 else "med-card-low"
                    badge_cls = "badge-high"   if conf > 80 else "badge-medium"  if conf > 50 else "badge-low"
                    link_html = f'<a href="{url}" target="_blank" style="color:#1a8754;font-weight:600">View on PharmeEasy ↗</a>' if url else '<span style="color:#dc3545">No link available</span>'

                    st.markdown(f"""
                    <div class="med-card {card_cls}">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.4rem">
                            <span class="med-name">💊 {i}. {med.get('name','Unknown')}</span>
                            <span class="badge {badge_cls}">{conf:.0f}% match</span>
                        </div>
                        <div class="med-meta">
                            <span><strong>Strength</strong> {med.get('strength','—')}</span>
                            <span><strong>Instructions</strong> {med.get('instructions','—')}</span>
                            <span><strong>Duration</strong> {med.get('duration','—')}</span>
                        </div>
                        <div style="margin-top:.5rem;font-size:.85rem">{link_html}</div>
                    </div>""", unsafe_allow_html=True)

                    all_products = med.get('all_products', [])
                    if all_products:
                        with st.expander(f"All {len(all_products)} product option(s)"):
                            for j, p in enumerate(all_products, 1):
                                purl = p.get('url', '')
                                label = f"**{p.get('name','Unknown')}**" + (" ⭐" if j == 1 else "")
                                if purl:
                                    st.markdown(f"{j}. {label} — [View]({purl})")
                                else:
                                    st.markdown(f"{j}. {label}")

                with st.expander("🔍 Raw JSON"):
                    st.json(fixed)

    # Download all as ZIP
    st.markdown("---")
    if st.button("📦 Download All Files as ZIP", use_container_width=True):
        create_download_zip(results)

def create_download_zip(results):
    """Create a ZIP file with all results"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add HTML summary
        if 'html_summary' in results and results['html_summary'] is not None:
            zip_file.writestr("discharge_summary.html", results['html_summary'])
        
        # Add markdown
        if 'markdown' in results and results['markdown'] is not None:
            zip_file.writestr("discharge.md", results['markdown'])
        
        # Add JSON files for available data
        import json
        for key in ['diagnoses', 'medications', 'fixed_medications']:
            if key in results and results[key] is not None:
                zip_file.writestr(f"{key}.json", json.dumps(results[key], indent=2))
        
        # Add a summary of what was processed
        summary_text = "Shusrusha Processing Summary\n" + "="*30 + "\n\n"
        summary_text += f"OCR: {'✅ Completed' if 'markdown' in results and results['markdown'] else '❌ Failed'}\n"
        summary_text += f"Diagnoses: {'✅ Completed' if results.get('diagnoses') is not None else '⏭️ Skipped'}\n"
        summary_text += f"Medications: {'✅ Completed' if results.get('medications') is not None else '⏭️ Skipped'}\n"
        summary_text += f"PharmeEasy Links: {'✅ Completed' if results.get('fixed_medications') is not None else '⏭️ Skipped'}\n"
        summary_text += f"HTML Summary: {'✅ Completed' if results.get('html_summary') is not None else '⏭️ Skipped'}\n"
        
        zip_file.writestr("processing_summary.txt", summary_text)
    
    zip_buffer.seek(0)
    
    st.download_button(
        label="📥 Download ZIP Package",
        data=zip_buffer.getvalue(),
        file_name="shusrusha_results.zip",
        mime="application/zip",
        use_container_width=True
    )

def show_about():
    """Show about information — kept for compatibility."""
    pass

# Sidebar — static about section (no button needed)
with st.sidebar:
    with st.expander("ℹ️ About Shusrusha"):
        st.markdown("""
**Shusrusha** converts hospital discharge summary images into interactive HTML reports with:

- 🔍 AI-powered OCR
- 🩺 Diagnosis extraction
- 💊 Medication extraction
- 🔗 PharmeEasy product matching
- 📋 Downloadable HTML report

**Stack:** LangGraph · OpenAI · Streamlit
        """)

if __name__ == "__main__":
    main()
