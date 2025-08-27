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
</style>
""", unsafe_allow_html=True)

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
            run_medications = st.checkbox("💊 Extract Medications", value=True, help="Extract prescribed medications")
        
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
        # File upload section
        st.markdown('<div class="step-header"><h3>📤 Step 1: Upload Discharge Summary Images</h3></div>', unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader(
            "Choose image files",
            type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'],
            accept_multiple_files=True,
            key="multi_file_uploader_v2",
            help="Upload multiple images of discharge summary pages. Supported formats: PNG, JPG, JPEG, GIF, BMP, TIFF"
        )
        
        if uploaded_files:
            st.markdown(f'<div class="success-box">✅ Uploaded {len(uploaded_files)} files</div>', unsafe_allow_html=True)
            
            # Show uploaded files with details
            total_size = 0
            for i, file in enumerate(uploaded_files, 1):
                file_size = file.size
                total_size += file_size
                size_mb = file_size / (1024 * 1024)
                st.write(f"{i}. **{file.name}** ({size_mb:.2f} MB)")
            
            st.write(f"**Total size:** {total_size / (1024 * 1024):.2f} MB")
            
            # File validation
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
    
    with col2:
        # Instructions
        st.markdown("### 📖 Instructions")
        st.markdown("""
        1. **Upload Images**: Select multiple images of your discharge summary
        2. **Configure**: Choose AI models and processing options
        3. **Process**: Click the button to start processing
        4. **Review**: Check the extracted information
        5. **Download**: Get your interactive HTML report
        
        **Supported formats**: PNG, JPG, JPEG, GIF, BMP, TIFF
        
        **Tips:**
        - 📸 Ensure images are clear and readable
        - 📑 Upload pages in the correct order
        - 🔧 Use gpt-4o for better accuracy
        - 💾 Enable file auto-opening for quick review
        """)
    
    # Processing section
    if uploaded_files:
        st.markdown('<div class="step-header"><h3>🔄 Step 2: Process Documents</h3></div>', unsafe_allow_html=True)
        
        if st.button("🚀 Start Processing", type="primary", use_container_width=True):
            process_documents(uploaded_files, ocr_model, extraction_model, pharmacy_model, 
                            save_files, open_files, show_debug, 
                            run_diagnoses, run_medications, run_pharmacy, run_summary)

def process_documents(uploaded_files, ocr_model, extraction_model, pharmacy_model, save_files, open_files, show_debug, 
                     run_diagnoses, run_medications, run_pharmacy, run_summary):
    """Process the uploaded documents through the entire pipeline"""
    
    # Initialize session state for results
    if 'processing_results' not in st.session_state:
        st.session_state.processing_results = {}
    
    try:
        # Validate uploaded files
        valid_files = [f for f in uploaded_files if f.size > 0]
        if not valid_files:
            st.error("❌ No valid files to process. Please upload valid image files.")
            return
        
        if len(valid_files) != len(uploaded_files):
            st.warning(f"⚠️ Processing {len(valid_files)} valid files out of {len(uploaded_files)} uploaded.")
        
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
            
            st.info(f"📁 Processing {len(image_paths)} image files...")
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: OCR
            status_text.text("🔍 Step 1/5: Processing OCR...")
            progress_bar.progress(0.2)
            
            with st.spinner("Extracting text from images..."):
                markdown = app_graph.run_node("OCR", image_paths, ocr_model)
                
                # Clean markdown
                markdown = clean_markdown(markdown)
                
                if save_files:
                    save_file("discharge.md", markdown)
                    st.success("✅ Markdown saved to discharge.md")
                    
                    if open_files:
                        open_result = open_file_in_system("discharge.md")
                        st.info(f"📂 {open_result}")
                
                st.session_state.processing_results['markdown'] = markdown
            
            if show_debug:
                with st.expander("📄 OCR Results"):
                    st.markdown(markdown)
            
            # Step 2: Extract Diagnoses (Optional)
            if run_diagnoses:
                status_text.text("🩺 Step 2/5: Extracting diagnoses...")
                progress_bar.progress(0.4)
                
                with st.spinner("Extracting medical diagnoses..."):
                    diagnoses = app_graph.run_node("ExtractDiagnoses", model=extraction_model)
                    st.session_state.processing_results['diagnoses'] = diagnoses
                
                if show_debug:
                    with st.expander("🩺 Diagnosed Conditions"):
                        st.json(diagnoses)
            else:
                st.info("⏭️ Skipping diagnoses extraction")
                st.session_state.processing_results['diagnoses'] = None
            
            # Step 3: Extract Medications (Optional)
            if run_medications:
                status_text.text("💊 Step 3/5: Extracting medications...")
                progress_bar.progress(0.6)
                
                with st.spinner("Extracting medications..."):
                    medications = app_graph.run_node("ExtractMedications", model=extraction_model)
                    st.session_state.processing_results['medications'] = medications
                
                if show_debug:
                    with st.expander("💊 Extracted Medications"):
                        st.json(medications)
            else:
                st.info("⏭️ Skipping medications extraction")
                st.session_state.processing_results['medications'] = None
            
            # Step 4: Fix Medications (Optional, depends on medications)
            if run_pharmacy:
                if run_medications:
                    status_text.text("🔗 Step 4/5: Matching medications with PharmeEasy...")
                    progress_bar.progress(0.8)
                    
                    with st.spinner("Finding medication links..."):
                        fixed_medications = app_graph.run_node("FixMedications", model=pharmacy_model)
                        st.session_state.processing_results['fixed_medications'] = fixed_medications
                    
                    if show_debug:
                        with st.expander("🔗 Medication Links"):
                            st.json(fixed_medications)
                else:
                    st.warning("⚠️ Cannot run PharmeEasy integration - medications extraction is disabled")
                    st.session_state.processing_results['fixed_medications'] = None
            else:
                st.info("⏭️ Skipping PharmeEasy integration")
                st.session_state.processing_results['fixed_medications'] = None
            
            # Step 5: Generate Summary (Optional)
            if run_summary:
                status_text.text("📋 Step 5/5: Generating interactive summary...")
                progress_bar.progress(1.0)
                
                with st.spinner("Creating interactive HTML report..."):
                    html_summary = app_graph.run_node("AddSummaryPills")
                    
                    if save_files:
                        save_file("summary.html", html_summary)
                        st.success("✅ HTML summary saved to summary.html")
                        
                        if open_files:
                            open_result = open_file_in_system("summary.html")
                            st.info(f"📂 {open_result}")
                    
                    st.session_state.processing_results['html_summary'] = html_summary
            else:
                st.info("⏭️ Skipping HTML summary generation")
                st.session_state.processing_results['html_summary'] = None
            
            status_text.text("✅ Processing completed successfully!")
            
            # Display results
            display_results()
            
    except Exception as e:
        st.error(f"❌ Error during processing: {str(e)}")
        if show_debug:
            st.exception(e)

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
    """Display the processing results"""
    if 'processing_results' not in st.session_state:
        return
    
    results = st.session_state.processing_results
    
    st.markdown('<div class="step-header"><h3>📊 Step 3: Results</h3></div>', unsafe_allow_html=True)
    
    # Results tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Summary", "📄 Markdown", "🩺 Diagnoses", "💊 Medications", "🔗 Medication Links"])
    
    with tab1:
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
            st.info("⏭️ HTML summary generation was skipped")
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
    
    with tab2:
        st.subheader("Extracted Text (Markdown)")
        if 'markdown' in results:
            st.markdown(results['markdown'])
            
            st.download_button(
                label="📥 Download Markdown",
                data=results['markdown'],
                file_name="discharge.md",
                mime="text/markdown",
                use_container_width=True
            )
    
    with tab3:
        st.subheader("Medical Diagnoses")
        if 'diagnoses' in results and results['diagnoses'] is not None:
            st.json(results['diagnoses'])
        else:
            st.info("⏭️ Diagnoses extraction was skipped or not available")
    
    with tab4:
        st.subheader("Extracted Medications")
        if 'medications' in results and results['medications'] is not None:
            st.json(results['medications'])
        else:
            st.info("⏭️ Medications extraction was skipped or not available")
    
    with tab5:
        st.subheader("Medications with PharmeEasy Links")
        if 'fixed_medications' in results and results['fixed_medications'] is not None:
            st.json(results['fixed_medications'])
        else:
            st.info("⏭️ PharmeEasy integration was skipped or not available")
    
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
    st.markdown("""
    **Shusrusha** is an AI-powered medical document processing application that transforms discharge summary images 
    into interactive, searchable HTML reports with medication links and comprehensive analysis.
    
        **Features:**
        - 🔍 **Enhanced OCR**: Advanced text extraction with automatic markdown cleaning
        - 📁 **Smart File Handling**: Auto-open saved files in default applications
        - 🖱️ **Improved File Selection**: Native OS dialogs with multi-format support
        - 🩺 **Medical Analysis**: AI-powered diagnosis and medication extraction
        - 🔗 **Pharmacy Integration**: Direct links to PharmeEasy for medication ordering
        - � **Cross-Platform**: Works on macOS, Windows, and Linux
        - 💾 **Multiple Export Formats**: HTML, Markdown, JSON, and ZIP downloads    **Technology Stack:**
    - LangGraph for workflow orchestration
    - OpenAI GPT models for AI processing
    - Streamlit for web interface
    - PharmeEasy integration for medication data
    """)

# Sidebar navigation
with st.sidebar:
    st.markdown("---")
    if st.button("ℹ️ About", use_container_width=True):
        show_about()

if __name__ == "__main__":
    main()
