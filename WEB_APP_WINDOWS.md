# 🌐 Web Application - Easiest Windows Solution

## The Problem with Executables
Building cross-platform executables is complex. The binary built on macOS won't run on Windows.

## ✅ Recommended Solution: Web Application

### Why Use the Web App?
- ✅ **Works on any OS** (Windows, macOS, Linux)
- ✅ **No installation required** 
- ✅ **Always up-to-date**
- ✅ **Easy to share** (just send a link)
- ✅ **Professional UI** with Streamlit

### Setup on Windows

#### Step 1: Install Python
1. Download Python 3.8+ from https://python.org/downloads/
2. **Important**: Check "Add Python to PATH" during installation
3. Restart your computer

#### Step 2: Download Shusrusha
1. Download this project as ZIP from GitHub
2. Extract to a folder like `C:\shusrusha\`

#### Step 3: Install Dependencies
```cmd
# Open Command Prompt (Win + R, type "cmd", press Enter)
cd C:\shusrusha
pip install -r requirements-app.txt
```

#### Step 4: Set API Key
Create a file named `.env` in the shusrusha folder:
```
OPENAI_API_KEY=your_openai_api_key_here
```

#### Step 5: Run the Web App
```cmd
streamlit run app.py
```

The app will open in your web browser at `http://localhost:8501`

### Using the Web App

1. **Upload Images**: Click "Browse files" to select discharge summary images
2. **OCR Processing**: Convert images to text automatically  
3. **Optional Steps**: Choose which analysis steps to run
4. **Download Results**: Get HTML summary and markdown files

### Sharing with Others

#### Option A: Local Network Sharing
```cmd
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```
Others can access at `http://YOUR_IP:8501`

#### Option B: Cloud Deployment
Deploy to:
- **Streamlit Cloud** (free): https://streamlit.io/cloud
- **Heroku**: https://heroku.com  
- **Railway**: https://railway.app
- **Render**: https://render.com

### Troubleshooting

#### "Python not found"
- Reinstall Python with "Add to PATH" checked
- Restart Command Prompt

#### "pip not found" 
```cmd
python -m pip install --upgrade pip
```

#### "ModuleNotFoundError"
```cmd
pip install -r requirements-app.txt
```

#### "OpenAI API Error"
- Check your `.env` file has the correct API key
- Verify at https://platform.openai.com/

#### "Port already in use"
```cmd
streamlit run app.py --server.port 8502
```

### Advantages over Executable
- **No file size limits** (executables can be 100MB+)
- **Easy updates** (just download new code)
- **Better error handling** (see errors in browser)
- **Mobile friendly** (works on phones/tablets)
- **Shareable** (multiple users can access)

### Creating a Desktop Shortcut

Create a `.bat` file named `Start Shusrusha.bat`:
```batch
@echo off
cd /d "C:\shusrusha"
streamlit run app.py
pause
```

Double-click this file to start the web app easily!
