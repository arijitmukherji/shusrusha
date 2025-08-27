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

def main():
    # Header
    st.markdown('<h1 class="main-header">🏥 Shusrusha Medical Document Processor</h1>', unsafe_allow_html=True)
    st.markdown("Convert discharge summary images into interactive HTML reports with medication analysis")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key check
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            st.success("✅ OpenAI API Key loaded")
        else:
            st.error("❌ OpenAI API Key not found")
            st.info("Add your OpenAI API key to a .env file:\n`OPENAI_API_KEY=your_key_here`")
            return
        
        # Model selection
        st.subheader("🤖 Model Configuration")
        ocr_model = st.selectbox(
            "OCR Model",
            ["gpt-4o", "gpt-4o-mini"],
            index=0,
            help="Model for image OCR processing"
        )
        
        extraction_model = st.selectbox(
            "Extraction Model",
            ["gpt-4o-mini", "gpt-4o"],
            index=0,
            help="Model for text extraction tasks"
        )
        
        pharmacy_model = st.selectbox(
            "Pharmacy Matching Model",
            ["gpt-4o", "gpt-4o-mini"],
            index=0,
            help="Model for medication matching with PharmeEasy"
        )
        
        # Processing options
        st.subheader("📋 Processing Options")
        save_files = st.checkbox("Save intermediate files", value=True, help="Save markdown and HTML files")
        open_files = st.checkbox("Open files in system apps", value=True, help="Automatically open saved files")
        show_debug = st.checkbox("Show debug information", value=False, help="Display detailed processing logs")
        
        # Processing steps configuration
        st.subheader("🔧 Processing Steps")
        st.markdown("Choose which steps to run after OCR:")
        
        col1, col2 = st.columns(2)
        with col1:
            run_diagnoses = st.checkbox("🩺 Extract Diagnoses", value=True, help="Extract medical conditions and diagnoses")
            run_medications = st.checkbox("💊 Extract Medications", value=True, help="Extract medication names, strengths, instructions and duration")
        
        with col2:
            run_pharmacy = st.checkbox("🔗 PharmeEasy Integration", value=True, help="Match medications with pharmacy links")
            run_summary = st.checkbox("📋 Generate HTML Summary", value=True, help="Create interactive HTML report")
        
        # Dependency warnings
        if run_pharmacy and not run_medications:
            st.warning("⚠️ PharmeEasy integration requires medication extraction to be enabled.")
        
        if run_summary and not (run_medications or run_diagnoses):
            st.info("💡 HTML summary will be more comprehensive with diagnoses and medications enabled.")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # File selection section
        # Initialize session state for file management
        if 'selected_files' not in st.session_state:
            st.session_state.selected_files = []
        if 'show_file_list' not in st.session_state:
            st.session_state.show_file_list = False
        
        # Ensure selected_files is always a list
        if not isinstance(st.session_state.selected_files, list):
            st.session_state.selected_files = []
        
        # Compact one-line interface with Select Files button and file count
        col_select, col_count, col_spacer = st.columns([2, 2, 6])
        
        with col_select:
            # Show file selection button
            if st.button("📤 Select Files", key="select_files_btn", help="Choose discharge summary images"):
                # Open file uploader in session state
                st.session_state.show_file_uploader = True
                st.rerun()
        
        with col_count:
            if st.session_state.selected_files:
                # Show clickable file count
                total_size = sum(f.size for f in st.session_state.selected_files) / (1024 * 1024)
                if st.button(f"{len(st.session_state.selected_files)} files ({total_size:.1f} MB)", 
                           key="file_count_btn", 
                           help="Click to view selected files"):
                    st.session_state.show_file_list = not st.session_state.show_file_list
                    st.rerun()
        
        # File uploader modal (shown when Select Files is clicked)
        if 'show_file_uploader' in st.session_state and st.session_state.show_file_uploader:
            st.markdown("---")
            with st.container():
                st.markdown("### 📤 Select Discharge Summary Images")
                
                # File uploader - when files are selected, they replace all existing files
                new_files = st.file_uploader(
                    "Choose files (will replace any previously selected files)",
                    type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'],
                    accept_multiple_files=True,
                    key="new_file_uploader",
                    help="Select discharge summary images (PNG, JPG, JPEG, GIF, BMP, TIFF)"
                )
                
                # Control buttons
                col_done, col_cancel = st.columns(2)
                with col_done:
                    if st.button("✅ Done", key="file_uploader_done"):
                        if new_files:
                            # Replace all existing files with new selection
                            st.session_state.selected_files = list(new_files)
                        st.session_state.show_file_uploader = False
                        st.rerun()
                with col_cancel:
                    if st.button("❌ Cancel", key="file_uploader_cancel"):
                        st.session_state.show_file_uploader = False
                        st.rerun()
            st.markdown("---")
        
        # File list display modal (read-only view of selected files)
        if st.session_state.show_file_list and st.session_state.selected_files:
            st.markdown("---")
            with st.container():
                st.markdown("### 📁 Selected Files")
                
                for i, file in enumerate(st.session_state.selected_files):
                    file_size = file.size / (1024 * 1024)
                    st.write(f"{i+1}. **{file.name}** ({file_size:.2f} MB)")
                
                # Close button
                if st.button("❌ Close", key="close_file_list"):
                    st.session_state.show_file_list = False
                    st.rerun()
            st.markdown("---")
        
        # File validation for selected files
        uploaded_files = st.session_state.selected_files
        if uploaded_files:
            valid_files = []
            invalid_files = []
            for file in uploaded_files:
                if file.size > 0:
                    valid_files.append(file)
                else:
                    invalid_files.append(file.name)
            
            if invalid_files:
                st.warning(f"⚠️ Empty files detected: {', '.join(invalid_files)}")
            
            if len(valid_files) != len(uploaded_files):
                st.info(f"Processing {len(valid_files)} valid files out of {len(uploaded_files)} uploaded.")
        else:
            uploaded_files = None
    
    with col2:
        # Clickable Instructions
        if 'show_instructions' not in st.session_state:
            st.session_state.show_instructions = False
        
        if st.button("📖 How to Use Instructions", use_container_width=True, help="Click to show/hide usage instructions"):
            st.session_state.show_instructions = not st.session_state.show_instructions
        
        # Show instructions modal when toggled
        if st.session_state.show_instructions:
            with st.container():
                st.markdown('<div class="instructions-modal">', unsafe_allow_html=True)
                st.markdown("### 📖 Instructions")
                st.markdown("1. **Select Files**: Click 'Select Files' to choose discharge summary images")
                st.markdown("2. **Configure**: Choose AI models and processing options in the sidebar")
                st.markdown("3. **Process**: Click 'Start Processing' to begin analysis")
                st.markdown("4. **Review**: Check the extracted information in the Results section")
                st.markdown("5. **Download**: Get your interactive HTML report")
                st.markdown("")
                st.markdown("**Supported formats**: PNG, JPG, JPEG, GIF, BMP, TIFF")
                st.markdown("")
                st.markdown("**Tips:**")
                st.markdown("- 📸 Ensure images are clear and readable")
                st.markdown("- 📑 Upload pages in the correct order")
                st.markdown("- 🔧 Use gpt-4o for better accuracy")
                st.markdown("- 💾 Enable file auto-opening for quick review")
                st.markdown("- 📊 Click the file count to view selected files")
                st.markdown("- 🔄 Selecting files again will replace previous selection")
                st.markdown('</div>', unsafe_allow_html=True)
    
    # Processing section
    if uploaded_files:
        st.markdown('<div class="step-header"><h3>🔄 Process Documents</h3></div>', unsafe_allow_html=True)
        
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
                    
                    # Create a nested container for all processing output
                    with st.container():
                        process_documents(uploaded_files, ocr_model, extraction_model, pharmacy_model, 
                                        save_files, open_files, show_debug, 
                                        run_diagnoses, run_medications, run_pharmacy, run_summary,
                                        processing_container)  # Pass the container to clear it later
        else:
            # Clear the processing container and show completion buttons
            with processing_container.container():
                # Show processing completed button
                col_completed, col_reprocess = st.columns([3, 1])
                with col_completed:
                    if st.button("✅ Processing Completed (click to view)", type="secondary", use_container_width=True):
                        st.session_state.show_processing_logs = not st.session_state.show_processing_logs
                with col_reprocess:
                    if st.button("🔄 Reprocess", type="primary", use_container_width=True):
                        # Reset state and reprocess
                        st.session_state.processing_completed = False
                        st.session_state.processing_logs = []
                        st.session_state.show_processing_logs = False
                        st.rerun()
        
        # Show processing logs modal when requested
        if st.session_state.show_processing_logs and st.session_state.processing_logs:
            with st.container():
                st.markdown("---")
                st.markdown("### 📋 Processing Logs")
                
                # Create a scrollable container for logs
                log_container = st.container()
                with log_container:
                    for log_entry in st.session_state.processing_logs:
                        if log_entry['type'] == 'info':
                            st.info(log_entry['message'])
                        elif log_entry['type'] == 'success':
                            st.success(log_entry['message'])
                        elif log_entry['type'] == 'warning':
                            st.warning(log_entry['message'])
                        elif log_entry['type'] == 'error':
                            st.error(log_entry['message'])
                        else:
                            st.write(log_entry['message'])
                
                # Close button
                if st.button("❌ Close Logs", key="close_processing_logs"):
                    st.session_state.show_processing_logs = False
                    st.rerun()
                
                st.markdown("---")

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
                     run_diagnoses, run_medications, run_pharmacy, run_summary, processing_container=None):
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
                markdown = app_graph.run_node("OCR", image_paths, ocr_model)
                
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
                    diagnoses = app_graph.run_node("ExtractDiagnoses", model=extraction_model)
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
                    medications = app_graph.run_node("ExtractMedications", model=extraction_model)
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
                        fixed_medications = app_graph.run_node("FixMedications", model=pharmacy_model)
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
                    html_summary = app_graph.run_node("AddSummaryPills")
                    
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
    """Display the processing results progressively as steps complete"""
    if 'processing_results' not in st.session_state:
        return
    
    results = st.session_state.processing_results
    
    # Only show results header if we have any results
    if not any(results.values()):
        return
    
    st.markdown('<div class="step-header"><h3>📊 Results</h3></div>', unsafe_allow_html=True)
    
    # Create tabs dynamically based on available results
    available_tabs = []
    tab_labels = []
    
    # Always show Summary tab if we have any results
    available_tabs.append("summary")
    tab_labels.append("📋 Summary")
    
    # Show Markdown tab if OCR is complete
    if 'markdown' in results and results['markdown']:
        available_tabs.append("markdown")
        tab_labels.append("📄 Markdown")
    
    # Show Diagnoses tab if diagnoses extraction is complete
    if 'diagnoses' in results and results['diagnoses'] is not None:
        available_tabs.append("diagnoses")
        tab_labels.append("🩺 Diagnoses")
    
    # Show Medications tab if medications extraction is complete
    if 'medications' in results and results['medications'] is not None:
        available_tabs.append("medications")
        tab_labels.append("💊 Medications")
    
    # Show Medication Links tab if PharmeEasy integration is complete
    if 'fixed_medications' in results and results['fixed_medications'] is not None:
        available_tabs.append("medication_links")
        tab_labels.append("🔗 Medication Links")
    
    # Create the tabs
    if len(available_tabs) == 1:
        # Special case for single tab
        tab_containers = [st.container()]
    else:
        tab_containers = st.tabs(tab_labels)
    
    # Display content for each available tab
    for i, (tab_type, container) in enumerate(zip(available_tabs, tab_containers)):
        with container:
            if tab_type == "summary":
                st.subheader("Interactive HTML Summary")
                if 'html_summary' in results and results['html_summary'] is not None:
                    # Display HTML summary
                    st.components.v1.html(results['html_summary'], height=600, scrolling=True)
                    
                    # Download button
                    st.download_button(
                        label="📥 Download HTML Report",
                        data=results['html_summary'],
                        file_name="discharge_summary.html",
                        mime="text/html",
                        use_container_width=True
                    )
                else:
                    st.info("⏭️ HTML summary generation was skipped or in progress")
                    st.markdown("**Available data:**")
                    
                    # Show what's available
                    if 'markdown' in results and results['markdown']:
                        st.markdown("- ✅ OCR Text (available in Markdown tab)")
                    if 'diagnoses' in results and results['diagnoses']:
                        st.markdown("- ✅ Medical Diagnoses")
                    if 'medications' in results and results['medications']:
                        st.markdown("- ✅ Extracted Medications")
                    if 'fixed_medications' in results and results['fixed_medications']:
                        st.markdown("- ✅ Pharmacy Links")
                        
            elif tab_type == "markdown":
                st.subheader("Extracted Text (Markdown)")
                st.markdown(results['markdown'])
                
                st.download_button(
                    label="📥 Download Markdown",
                    data=results['markdown'],
                    file_name="discharge.md",
                    mime="text/markdown",
                    use_container_width=True
                )
                
            elif tab_type == "diagnoses":
                st.subheader("Medical Diagnoses")
                if 'diagnoses' in results and results['diagnoses'] is not None:
                    diagnoses_data = results['diagnoses']
                    
                    # Summary section
                    diag_count = len(diagnoses_data.get('diagnoses', []))
                    lab_count = len(diagnoses_data.get('lab_tests', []))
                    
                    col_summary1, col_summary2, col_summary3 = st.columns(3)
                    with col_summary1:
                        st.metric("🩺 Total Diagnoses", diag_count)
                    with col_summary2:
                        st.metric("🧪 Total Lab Tests", lab_count)
                    with col_summary3:
                        st.metric("📊 Total Items", diag_count + lab_count)
                    
                    st.markdown("---")
                    
                    # Create two columns for diagnoses and lab tests
                    col_diag, col_lab = st.columns(2)
                    
                    with col_diag:
                        st.markdown("#### 🩺 Diagnoses")
                        if 'diagnoses' in diagnoses_data and diagnoses_data['diagnoses']:
                            for i, diagnosis in enumerate(diagnoses_data['diagnoses'], 1):
                                st.markdown(f'<div class="diagnosis-item">{i}. **{diagnosis}**</div>', unsafe_allow_html=True)
                        else:
                            st.info("No diagnoses found")
                    
                    with col_lab:
                        st.markdown("#### 🧪 Lab Tests")
                        if 'lab_tests' in diagnoses_data and diagnoses_data['lab_tests']:
                            for i, lab_test in enumerate(diagnoses_data['lab_tests'], 1):
                                st.markdown(f'<div class="lab-test-item">{i}. **{lab_test}**</div>', unsafe_allow_html=True)
                        else:
                            st.info("No lab tests found")
                    
                    # Show raw JSON data in an expander for debugging
                    with st.expander("🔍 View Raw Data (Debug)"):
                        st.json(diagnoses_data)
                else:
                    st.info("⏳ Diagnoses extraction in progress...")
            
            elif tab_type == "medications":
                st.subheader("Extracted Medications")
                if 'medications' in results and results['medications'] is not None:
                    medications_data = results['medications']
                    
                    # Summary metrics
                    medications_list = medications_data.get('medications', [])
                    meds_count = len(medications_list)
                    
                    col_summary1, col_summary2, col_summary3 = st.columns(3)
                    with col_summary1:
                        st.metric("💊 Total Medications", meds_count)
                    with col_summary2:
                        with_duration = len([m for m in medications_list if m.get('duration') and m.get('duration').lower() not in ['continue', 'as needed', '']])
                        st.metric("⏰ With Duration", with_duration)
                    with col_summary3:
                        as_needed = len([m for m in medications_list if m.get('duration') and 'as needed' in m.get('duration', '').lower()])
                        st.metric("🔄 As Needed", as_needed)
                    
                    st.markdown("---")
                    
                    # Display medications in cards
                    if medications_list:
                        for i, med in enumerate(medications_list, 1):
                            with st.container():
                                st.markdown(f"""
                                <div class="medication-card">
                                    <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                                        <h4 style="margin: 0; color: #2E8B57;">💊 {i}. {med.get('name', 'Unknown Medication')}</h4>
                                    </div>
                                    <div style="margin-left: 1rem;">
                                        <p style="margin: 0.25rem 0;"><strong>⚖️ Strength:</strong> {med.get('strength', 'Not specified')}</p>
                                        <p style="margin: 0.25rem 0;"><strong>📋 Instructions:</strong> {med.get('instructions', 'No instructions provided')}</p>
                                        <p style="margin: 0.25rem 0;"><strong>⏱️ Duration:</strong> {med.get('duration', 'Not specified')}</p>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.info("No medications found")
                    
                    # Show raw JSON data in an expander for debugging
                    with st.expander("🔍 View Raw Data (Debug)"):
                        st.json(medications_data)
                else:
                    st.info("⏳ Medications extraction in progress...")
            
            elif tab_type == "medication_links":
                st.subheader("Medications with PharmeEasy Links")
                if 'fixed_medications' in results and results['fixed_medications'] is not None:
                    fixed_medications_data = results['fixed_medications']
                    fixed_meds_list = fixed_medications_data.get('medications', [])
                    
                    # Summary metrics
                    total_meds = len(fixed_meds_list)
                    high_confidence = len([m for m in fixed_meds_list if m.get('selection_confidence', 0) > 80])
                    with_links = len([m for m in fixed_meds_list if m.get('pharmaeasy_url')])
                    no_matches = len([m for m in fixed_meds_list if len(m.get('all_products', [])) == 0])
                    
                    col_summary1, col_summary2, col_summary3, col_summary4 = st.columns(4)
                    with col_summary1:
                        st.metric("💊 Total Medications", total_meds)
                    with col_summary2:
                        st.metric("✅ High Confidence", high_confidence, help="Confidence > 80%")
                    with col_summary3:
                        st.metric("🔗 With Links", with_links)
                    with col_summary4:
                        st.metric("❌ No Matches", no_matches)
                    
                    st.markdown("---")
                    
                    # Display medications with enhanced information
                    if fixed_meds_list:
                        for i, med in enumerate(fixed_meds_list, 1):
                            confidence = med.get('selection_confidence', 0)
                            pharmaeasy_url = med.get('pharmaeasy_url', '')
                            all_products = med.get('all_products', [])
                            
                            # If main pharmaeasy_url is missing but we have products, use the first product's URL
                            if not pharmaeasy_url and all_products:
                                pharmaeasy_url = all_products[0].get('url', '')
                            
                            # Determine card color based on confidence and availability
                            if confidence > 80:
                                card_class = "medication-card-high"
                            elif confidence > 50:
                                card_class = "medication-card-medium"
                            else:
                                card_class = "medication-card-low"
                            
                            with st.container():
                                # Main medication card
                                st.markdown(f"""
                                <div class="{card_class}">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                                        <h4 style="margin: 0; color: #2E8B57;">💊 {i}. {med.get('name', 'Unknown Medication')}</h4>
                                        <span style="background: {'#28a745' if confidence > 80 else '#ffc107' if confidence > 50 else '#dc3545'}; color: white; padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.8rem; font-weight: bold;">
                                            {confidence:.0f}% confidence
                                        </span>
                                    </div>
                                    <div style="margin-left: 1rem;">
                                        <p style="margin: 0.25rem 0;"><strong>⚖️ Strength:</strong> {med.get('strength', 'Not specified')}</p>
                                        <p style="margin: 0.25rem 0;"><strong>📋 Instructions:</strong> {med.get('instructions', 'No instructions provided')}</p>
                                        <p style="margin: 0.25rem 0;"><strong>⏱️ Duration:</strong> {med.get('duration', 'Not specified')}</p>
                                """, unsafe_allow_html=True)
                                
                                # PharmeEasy link if available
                                if pharmaeasy_url:
                                    st.markdown(f'<p style="margin: 0.25rem 0;"><strong>🔗 PharmeEasy:</strong> <a href="{pharmaeasy_url}" target="_blank" style="color: #007bff; text-decoration: none;">View Product</a></p>', unsafe_allow_html=True)
                                else:
                                    st.markdown('<p style="margin: 0.25rem 0; color: #dc3545;"><strong>⚠️ PharmeEasy:</strong> No direct link available</p>', unsafe_allow_html=True)
                                
                                # Alternative products if available
                                total_products = len(all_products)
                                if total_products > 0:
                                    st.markdown(f'<p style="margin: 0.25rem 0;"><strong>🔄 Available Options:</strong> {total_products} product(s) found</p>', unsafe_allow_html=True)
                                else:
                                    st.markdown('<p style="margin: 0.25rem 0; color: #dc3545;"><strong>⚠️ Status:</strong> No matching products found</p>', unsafe_allow_html=True)
                                
                                st.markdown('</div></div>', unsafe_allow_html=True)
                                
                                # Show all products in expandable section
                                if total_products > 0:
                                    with st.expander(f"View all {total_products} available product(s)"):
                                        for j, product in enumerate(all_products, 1):
                                            col_prod, col_link = st.columns([3, 1])
                                            with col_prod:
                                                product_name = product.get('name', 'Unknown Product')
                                                # Highlight the selected/main product
                                                if j == 1:  # Assuming first product is the selected one
                                                    st.write(f"{j}. **{product_name}** ⭐ *(Selected)*")
                                                else:
                                                    st.write(f"{j}. **{product_name}**")
                                            with col_link:
                                                product_url = product.get('url', '')
                                                if product_url:
                                                    st.markdown(f'<a href="{product_url}" target="_blank" style="color: #007bff;">View</a>', unsafe_allow_html=True)
                                                else:
                                                    st.write("No link")
                    else:
                        st.info("No medications with pharmacy links found")
                    
                    # Show raw JSON data in an expander for debugging
                    with st.expander("🔍 View Raw Data (Debug)"):
                        st.json(fixed_medications_data)
                else:
                    st.info("⏳ PharmeEasy integration in progress...")
    
    # Download all files as ZIP
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
    """Show about information"""
    st.markdown("### 🏥 About Shusrusha")
    st.write("**Shusrusha** is an AI-powered medical document processing application that transforms discharge summary images into interactive, searchable HTML reports with medication links and comprehensive analysis.")
    st.write("")
    st.write("**Features:**")
    st.write("- 🔍 **Enhanced OCR**: Advanced text extraction with automatic markdown cleaning")
    st.write("- 📁 **Smart File Handling**: Auto-open saved files in default applications")
    st.write("- 🖱️ **Improved File Selection**: Native OS dialogs with multi-format support")
    st.write("- 🩺 **Medical Analysis**: AI-powered diagnosis and medication extraction")
    st.write("- 🔗 **Pharmacy Integration**: Direct links to PharmeEasy for medication ordering")
    st.write("- 🌐 **Cross-Platform**: Works on macOS, Windows, and Linux")
    st.write("- 💾 **Multiple Export Formats**: HTML, Markdown, JSON, and ZIP downloads")
    st.write("")
    st.write("**Technology Stack:**")
    st.write("- LangGraph for workflow orchestration")
    st.write("- OpenAI GPT models for AI processing")
    st.write("- Streamlit for web interface")
    st.write("- PharmeEasy integration for medication data")

# Sidebar navigation
with st.sidebar:
    st.markdown("---")
    if st.button("ℹ️ About", use_container_width=True):
        show_about()

if __name__ == "__main__":
    main()
