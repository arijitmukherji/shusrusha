"""
Local API Server for Shusrusha
Runs on your local machine with your API keys
Serves requests from the cloud Streamlit app
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import base64
import tempfile
import json
from datetime import datetime
from dotenv import load_dotenv
import logging

# Import your existing processing functions
try:
    from langgraph_app import process_images_pipeline
    from lib.graph_utils import GraphState
except ImportError:
    print("Warning: Could not import processing functions. Using mock responses.")
    process_images_pipeline = None

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, origins=["*"])  # Allow requests from cloud app

# Rate limiting
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour", "10 per minute"]
)

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LOCAL_API_SECRET = os.getenv("LOCAL_API_SECRET", "your-secret-key-here")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def authenticate_request():
    """Check if request is authenticated"""
    auth_header = request.headers.get('Authorization', '')
    expected_auth = f"Bearer {LOCAL_API_SECRET}"
    
    if auth_header != expected_auth:
        return False
    return True

def log_request(action, details=None):
    """Log API requests for monitoring"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "ip": get_remote_address(),
        "details": details or {}
    }
    logger.info(f"API_REQUEST: {json.dumps(log_entry)}")

@app.before_request
def before_request():
    """Authentication and logging for all requests"""
    if request.endpoint == 'health_check':
        return  # Allow health checks without auth
    
    if not authenticate_request():
        log_request("unauthorized_access", {"endpoint": request.endpoint})
        return jsonify({"error": "Unauthorized access"}), 401

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "shusrusha-local-api",
        "timestamp": datetime.now().isoformat(),
        "openai_key_configured": bool(OPENAI_API_KEY)
    })

@app.route('/process', methods=['POST'])
@limiter.limit("5 per minute")
def process_document():
    """Process medical document using local API key"""
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract parameters
        image_data = data.get('image_data')
        options = data.get('options', {})
        model = data.get('model', 'gpt-4o-mini')
        
        if not image_data:
            return jsonify({"error": "No image data provided"}), 400
        
        log_request("processing_started", {
            "options": options,
            "model": model,
            "image_size": len(image_data)
        })
        
        # Decode base64 image
        try:
            image_bytes = base64.b64decode(image_data)
            
            if len(image_bytes) > MAX_FILE_SIZE:
                return jsonify({"error": f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB"}), 400
            
        except Exception as e:
            return jsonify({"error": f"Invalid image data: {str(e)}"}), 400
        
        # Save image to temporary file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(image_bytes)
            temp_file_path = temp_file.name
        
        try:
            # Process using your existing pipeline
            if process_images_pipeline:
                # Create initial state
                initial_state = GraphState(
                    images=[temp_file_path],
                    markdown="",
                    diagnoses={},
                    medications={},
                    fixed_medications={},
                    html_summary=""
                )
                
                # Run processing pipeline
                result_state = process_images_pipeline(initial_state, model)
                
                # Prepare response
                response = {
                    "status": "success",
                    "markdown": result_state.get("markdown", ""),
                    "diagnoses": result_state.get("diagnoses", {}),
                    "medications": result_state.get("medications", {}),
                    "fixed_medications": result_state.get("fixed_medications", {}),
                    "html_summary": result_state.get("html_summary", ""),
                    "processing_model": model,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # Mock response for testing
                response = {
                    "status": "success",
                    "markdown": "# Sample OCR Output\n\nPatient discharge summary processed successfully.\n\n## Key Information\n- Date: Sample date\n- Patient: Sample patient\n- Diagnosis: Sample diagnosis",
                    "diagnoses": {
                        "conditions": ["Hypertension", "Diabetes Type 2"],
                        "lab_tests": ["Blood glucose", "Blood pressure monitoring"]
                    },
                    "medications": {
                        "medications": [
                            {"name": "Metformin", "dosage": "500mg", "frequency": "Twice daily"},
                            {"name": "Lisinopril", "dosage": "10mg", "frequency": "Once daily"}
                        ]
                    },
                    "fixed_medications": {
                        "matched_medications": [
                            {
                                "name": "Metformin",
                                "pharmeasy_url": "https://pharmeasy.in/search/all?name=metformin",
                                "confidence": 0.9
                            }
                        ]
                    },
                    "html_summary": """
                    <h1>Medical Discharge Summary</h1>
                    <h2>Diagnoses</h2>
                    <ul><li>Hypertension</li><li>Diabetes Type 2</li></ul>
                    <h2>Medications</h2>
                    <div class="medication-pill">
                        <a href="https://pharmeasy.in/search/all?name=metformin" target="_blank">
                            Metformin 500mg - Twice daily
                        </a>
                    </div>
                    """,
                    "processing_model": model,
                    "timestamp": datetime.now().isoformat(),
                    "mock_response": True
                }
            
            log_request("processing_completed", {
                "success": True,
                "model": model,
                "has_diagnoses": bool(response.get("diagnoses")),
                "has_medications": bool(response.get("medications"))
            })
            
            return jsonify(response)
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
    
    except Exception as e:
        error_msg = str(e)
        log_request("processing_failed", {"error": error_msg})
        logger.error(f"Processing error: {error_msg}")
        return jsonify({"error": f"Processing failed: {error_msg}"}), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get API server status and statistics"""
    return jsonify({
        "status": "running",
        "openai_configured": bool(OPENAI_API_KEY),
        "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
        "rate_limits": {
            "requests_per_hour": 100,
            "requests_per_minute": 10,
            "processing_per_minute": 5
        },
        "timestamp": datetime.now().isoformat()
    })

@app.errorhandler(429)
def handle_rate_limit(e):
    """Handle rate limit exceeded"""
    log_request("rate_limit_exceeded", {"limit": str(e)})
    return jsonify({
        "error": "Rate limit exceeded",
        "message": "Too many requests. Please wait before trying again.",
        "retry_after": e.retry_after
    }), 429

@app.errorhandler(500)
def handle_server_error(e):
    """Handle server errors"""
    log_request("server_error", {"error": str(e)})
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred. Please try again."
    }), 500

def main():
    """Main function to start the API server"""
    if not OPENAI_API_KEY:
        print("❌ ERROR: OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key in the .env file")
        return
    
    print("🏥 Starting Shusrusha Local API Server")
    print("=" * 50)
    print(f"✅ OpenAI API Key: {'*' * 20}{OPENAI_API_KEY[-4:]}")
    print(f"✅ Authentication: {'Enabled' if LOCAL_API_SECRET != 'your-secret-key-here' else 'Disabled (update LOCAL_API_SECRET)'}")
    print(f"✅ Max file size: {MAX_FILE_SIZE // (1024*1024)}MB")
    print(f"✅ Processing pipeline: {'Available' if process_images_pipeline else 'Mock mode'}")
    print()
    print("🌐 Server will be available at:")
    print("   Local:  http://localhost:5000")
    print("   Network: http://YOUR_IP:5000")
    print()
    print("🔧 To use with ngrok:")
    print("   1. Install ngrok: https://ngrok.com/")
    print("   2. Run: ngrok http 5000")
    print("   3. Use the HTTPS URL in your cloud app")
    print()
    print("🛑 Press Ctrl+C to stop")
    print()
    
    # Start Flask server
    app.run(
        host='0.0.0.0',  # Allow external connections
        port=5000,
        debug=False,
        threaded=True
    )

if __name__ == '__main__':
    main()
