# 🔐 Security Configuration Guide

## Environment Variable Management

Shusrusha uses environment variables for secure API key management. **No secrets are stored in the repository or Docker images.**

## 📁 File Structure

### Local Development
```
shusrusha/
├── .env                          # ❌ NOT in git - your actual secrets
├── .streamlit/
│   ├── config.toml              # ✅ In git - app configuration
│   └── secrets.toml.template    # ✅ In git - template only
└── docker-compose.yml           # ✅ In git - reads from .env
```

### Security Files Status
- ✅ `.env` - **IGNORED by git** (contains real secrets)
- ✅ `secrets.toml` - **DELETED and IGNORED by git**
- ✅ `secrets.toml.template` - **Template only, no real secrets**

## 🔧 Setup Instructions

### 1. Local Development (.env method)

Create a `.env` file in the project root:
```bash
# .env file (NOT committed to git)
OPENAI_API_KEY=your-openai-api-key-here
```

The application will automatically load this file using `python-dotenv`.

### 2. Docker Deployment

Docker Compose automatically reads from your `.env` file:
```yaml
# docker-compose.yml
environment:
  - OPENAI_API_KEY=${OPENAI_API_KEY}  # Loaded from .env
```

### 3. Streamlit Cloud Deployment

For Streamlit Cloud, add secrets in the web interface:
1. Go to your app's settings
2. Click "Secrets"
3. Add your secrets using the template from `secrets.toml.template`

## 🛡️ Security Features

### Git Protection
```gitignore
# .gitignore
.env
.env.*
.streamlit/secrets.toml
.streamlit/secrets.*
```

### Docker Protection
```dockerignore
# .dockerignore
*.env
.env*
.streamlit/secrets.toml
.streamlit/secrets.*
secrets.*
```

### Application Security
- ✅ Uses `os.getenv()` for environment variables
- ✅ No hardcoded API keys in source code
- ✅ No secrets files in Docker images
- ✅ Environment variables only passed at runtime

## 🔄 Migration from secrets.toml

If you previously used `secrets.toml`:

1. **Create .env file** with your secrets:
   ```bash
   echo "OPENAI_API_KEY=your-actual-api-key" > .env
   ```

2. **Remove old secrets file**:
   ```bash
   rm .streamlit/secrets.toml
   ```

3. **Rebuild Docker container**:
   ```bash
   docker-compose up --build -d
   ```

## ✅ Verification

Check that secrets are properly configured:

### Local Check
```bash
# Verify .env is loaded
python -c "import os; print('API Key loaded:', bool(os.getenv('OPENAI_API_KEY')))"
```

### Docker Check
```bash
# Verify container has environment variables
docker exec shusrusha-app env | grep OPENAI_API_KEY
```

### Security Check
```bash
# Verify no secrets in git
git ls-files | grep -E "(\.env|secret)" || echo "✅ No secrets tracked"

# Verify no secrets in Docker image
docker exec shusrusha-app find /app -name "*secret*" -name "*.env*" | grep -v python || echo "✅ No secrets in container"
```

## 🚨 Security Best Practices

### DO ✅
- Use `.env` file for local development
- Use environment variables in production
- Keep API keys in cloud provider secret managers
- Rotate API keys regularly
- Use different keys for dev/staging/prod

### DON'T ❌
- Commit `.env` files to git
- Put secrets in `secrets.toml` in git
- Hardcode API keys in source code
- Share API keys in chat/email
- Use production keys in development

## 🔧 Environment Variables

### Required
```bash
OPENAI_API_KEY=your-openai-api-key-here  # Your OpenAI API key
```

### Optional
```bash
RATE_LIMIT_DOCS_HOUR=5      # Hourly document limit
RATE_LIMIT_DOCS_DAY=20      # Daily document limit
MAX_FILE_SIZE_MB=10         # Maximum file size
```

## 🆘 Troubleshooting

### Issue: "API key not found"
1. Check `.env` file exists in project root
2. Verify API key format starts with `sk-`
3. Restart Docker container: `docker-compose restart`

### Issue: "Invalid API key"
1. Verify API key is correct in `.env`
2. Check API key hasn't expired
3. Test key directly: `curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models`

### Issue: "Permission denied"
1. Check `.env` file permissions: `chmod 600 .env`
2. Verify Docker has access to environment variables

## 📞 Security Contact

For security-related issues:
- Create a GitHub issue with `[SECURITY]` prefix
- Do not include actual API keys in issue reports
- Use placeholder values like `your-api-key-here` in examples

---

🔐 **Remember**: Never commit real API keys to git repositories!
