#!/bin/bash

# Shusrusha Medical Document Processor - Run Script
# This script starts the standalone application

echo "🏥 Starting Shusrusha Medical Document Processor..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if .env file exists and has API key
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please run setup.sh first."
    exit 1
fi

# Check if API key is set
if ! grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
    echo "⚠️  Warning: OpenAI API key may not be set in .env file"
    echo "Please make sure your .env file contains:"
    echo "OPENAI_API_KEY=your_actual_api_key_here"
    echo ""
fi

# Start the application
echo "🚀 Launching web application..."
echo "📱 The app will open in your browser at: http://localhost:8501"
echo "🛑 Press Ctrl+C to stop the application"
echo ""

streamlit run app.py
