# 🏥 Shusrusha Medical Document Processor

A standalone web application that converts discharge summary images into interactive HTML reports with medication links and analysis.

## 🚀 Quick Start

### 1. Setup (One-time)
```bash
./setup.sh
```

### 2. Configure API Key
Edit the `.env` file and add your OpenAI API key:
```
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Run the Application
```bash
./run.sh
```

The web app will open at `http://localhost:8501`

## 📱 Using the Web App

1. **Upload Images**: Drag and drop or select discharge summary images
2. **Configure Models**: Choose OpenAI models for different processing steps
3. **Process**: Click "Start Processing" to begin the AI pipeline
4. **Review Results**: View extracted text, diagnoses, and medications
5. **Download**: Get your interactive HTML report and source files

## 🛠 Manual Setup (Alternative)

If you prefer manual setup:

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements-app.txt

# Create .env file
echo "OPENAI_API_KEY=your_api_key_here" > .env

# Run the app
streamlit run app.py
```

## 📋 Features

### 🔍 **OCR Processing**
- Extract text from medical images using GPT-4 Vision
- Support for multiple image formats (PNG, JPG, JPEG, GIF, BMP, TIFF)
- Optimized for Indian medical documents

### 🩺 **Medical Analysis**
- Identify diagnoses and medical conditions
- Extract lab test results and values
- Parse medical terminology and abbreviations

### 💊 **Medication Processing**
- Extract prescribed medications with dosages
- Parse complex medication instructions
- Handle Indian medical notation (e.g., "Tab" vs "76")

### 🔗 **Pharmacy Integration**
- Match medications with PharmeEasy products
- Generate direct purchase links
- Provide alternative medication suggestions

### 📋 **Interactive Reports**
- Generate clean HTML summaries
- Clickable medication pills for easy ordering
- Mobile-responsive design
- Downloadable reports in multiple formats

## ⚙️ Configuration Options

### Model Selection
- **OCR Model**: `gpt-4o` (recommended) or `gpt-4o-mini`
- **Extraction Model**: `gpt-4o-mini` (cost-effective) or `gpt-4o`
- **Pharmacy Model**: `gpt-4o` (better accuracy) or `gpt-4o-mini`

### Processing Options
- Save intermediate files (markdown, JSON)
- Debug mode for detailed logging
- Batch processing for multiple documents

## 📁 Output Files

The application generates several output files:

- `discharge_summary.html` - Interactive HTML report
- `discharge.md` - Extracted text in markdown format
- `diagnoses.json` - Structured medical diagnoses
- `medications.json` - Extracted medications data
- `fixed_medications.json` - Medications with pharmacy links
- `shusrusha_results.zip` - Complete package download

## 🔒 Privacy & Security

- All processing happens locally on your machine
- Images are temporarily stored and automatically deleted
- No data is sent to external servers except OpenAI API
- API keys are stored locally in `.env` file

## 🏥 Medical Context

This application is optimized for:
- Indian medical practices and terminology
- Kolkata-based medical institutions
- Indian pharmaceutical products and brands
- Local medication availability through PharmeEasy

## 🆘 Troubleshooting

### Common Issues

**API Key Error**
```
❌ OpenAI API Key not found
```
**Solution**: Make sure your `.env` file contains a valid OpenAI API key.

**Import Errors**
```
ModuleNotFoundError: No module named 'streamlit'
```
**Solution**: Run `./setup.sh` to install all dependencies.

**File Upload Issues**
```
Error processing images
```
**Solution**: Ensure images are in supported formats and not corrupted.

### Getting Help

1. Check the debug mode in the sidebar for detailed error information
2. Ensure all dependencies are installed correctly
3. Verify your OpenAI API key has sufficient credits
4. Make sure images are clear and readable

## 🚀 Deployment Options

### Local Development
- Use `./run.sh` for local testing and development
- Access at `http://localhost:8501`

### Production Deployment

**Streamlit Cloud**
1. Push your code to GitHub
2. Connect to Streamlit Cloud
3. Add OpenAI API key in secrets
4. Deploy with one click

**Docker Deployment**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements-app.txt .
RUN pip install -r requirements-app.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

**Cloud Platforms**
- Deploy on Heroku, AWS, Google Cloud, or Azure
- Use environment variables for API keys
- Configure proper health checks

## 🔧 Advanced Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your_api_key_here
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### Custom Styling
Modify the CSS in `app.py` to customize the appearance:
```python
st.markdown("""
<style>
    .main-header { color: #your_color; }
    /* Add your custom styles */
</style>
""", unsafe_allow_html=True)
```

## 📈 Performance Tips

1. **Use appropriate models**: `gpt-4o-mini` for cost-effectiveness, `gpt-4o` for accuracy
2. **Optimize images**: Compress large images before upload
3. **Batch processing**: Process multiple pages together for efficiency
4. **Cache results**: Save intermediate results to avoid reprocessing

## 🤝 Contributing

This is a standalone version of the Shusrusha medical document processor. For the full development environment, see the notebook version in `discharge.ipynb`.

## 📄 License

This application is designed for medical document processing and should be used in compliance with relevant healthcare data protection regulations.

---

**Made with ❤️ for healthcare professionals in India**
