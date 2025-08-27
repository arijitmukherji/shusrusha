#!/bin/bash

# Shusrusha Hybrid Deployment Setup Script
# This script helps you set up the hybrid cloud-local deployment

echo "🏥 Shusrusha Hybrid Deployment Setup"
echo "===================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ and try again."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip is not installed. Please install pip and try again."
    exit 1
fi

echo "✅ pip found"

# Install local API server dependencies
echo
echo "📦 Installing local API server dependencies..."
pip3 install -r requirements-local-api.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Check for .env file
if [ ! -f .env ]; then
    echo
    echo "⚠️  No .env file found. Creating one now..."
    
    read -p "Enter your OpenAI API key: " openai_key
    read -p "Enter a secret key for API authentication (or press Enter for default): " api_secret
    
    if [ -z "$api_secret" ]; then
        api_secret="hybrid-$(openssl rand -hex 16)"
    fi
    
    cat > .env << EOF
# OpenAI API Configuration
OPENAI_API_KEY=$openai_key

# Local API Server Configuration
LOCAL_API_SECRET=$api_secret

# Optional: Customize rate limits
RATE_LIMIT_DOCS_HOUR=10
RATE_LIMIT_DOCS_DAY=50
MAX_FILE_SIZE_MB=10
EOF
    
    echo "✅ Created .env file with your configuration"
else
    echo "✅ .env file already exists"
fi

# Check if ngrok is installed
echo
echo "🔍 Checking for ngrok..."
if command -v ngrok &> /dev/null; then
    echo "✅ ngrok found: $(ngrok version)"
    
    echo
    echo "🚀 Starting local API server..."
    echo "   (This will run in the background)"
    
    # Start the local API server in the background
    nohup python3 local_api_server.py > local_api.log 2>&1 &
    API_PID=$!
    
    sleep 3
    
    # Check if server started successfully
    if ps -p $API_PID > /dev/null; then
        echo "✅ Local API server started (PID: $API_PID)"
        echo "📄 Logs: tail -f local_api.log"
        
        echo
        echo "🌐 Starting ngrok tunnel..."
        
        # Start ngrok
        ngrok http 5000 > /dev/null &
        NGROK_PID=$!
        
        sleep 3
        
        # Get ngrok URL
        NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    tunnel = data['tunnels'][0]
    print(tunnel['public_url'])
except:
    print('ERROR')
" 2>/dev/null)
        
        if [ "$NGROK_URL" != "ERROR" ] && [ ! -z "$NGROK_URL" ]; then
            echo "✅ ngrok tunnel created: $NGROK_URL"
            
            echo
            echo "🎉 Setup Complete!"
            echo "=================="
            echo
            echo "Your local API server is running at:"
            echo "  Local:  http://localhost:5000"
            echo "  Public: $NGROK_URL"
            echo
            echo "🌐 Cloud App Setup:"
            echo "1. Deploy app_hybrid_cloud.py to Streamlit Cloud"
            echo "2. Add these secrets to your Streamlit Cloud app:"
            echo "   LOCAL_API_URL = \"$NGROK_URL\""
            echo "   LOCAL_API_SECRET = \"$(grep LOCAL_API_SECRET .env | cut -d'=' -f2)\""
            echo
            echo "🛑 To stop services:"
            echo "   kill $API_PID $NGROK_PID"
            echo
            echo "📊 Monitor logs:"
            echo "   tail -f local_api.log"
            
        else
            echo "❌ Failed to create ngrok tunnel"
            echo "You can still access locally at http://localhost:5000"
            kill $NGROK_PID 2>/dev/null
        fi
        
    else
        echo "❌ Failed to start local API server"
        echo "Check local_api.log for error details"
    fi
    
else
    echo "⚠️  ngrok not found. You can:"
    echo "1. Install ngrok from https://ngrok.com/"
    echo "2. Or manually run: python3 local_api_server.py"
    echo "3. Then set up port forwarding on your router"
    
    echo
    echo "🚀 Starting local API server manually..."
    python3 local_api_server.py
fi
