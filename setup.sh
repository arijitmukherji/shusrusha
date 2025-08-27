#!/bin/bash

# Shusrusha Medical Document Processor - Installation Script
# This script sets up the standalone application

echo "🏥 Setting up Shusrusha Medical Document Processor..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.8 or higher from https://python.org"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements-app.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file..."
    echo "# Add your OpenAI API key here" > .env
    echo "OPENAI_API_KEY=your_openai_api_key_here" >> .env
    echo "❗ Please edit .env file and add your OpenAI API key"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file and add your OpenAI API key"
echo "2. Run: ./run.sh"
echo ""
echo "Or manually:"
echo "1. source .venv/bin/activate"
echo "2. streamlit run app.py"
